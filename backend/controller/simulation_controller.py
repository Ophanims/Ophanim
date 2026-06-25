import asyncio
from contextlib import suppress
from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder

from core.simulation_engine import SimulatorEngine
from controller.record_controller import get_record_series, list_records, delete_record, delete_records_by_project
from controller.project_controller import GroundStationBase, ProjectBase, fetch_project_by_id, get_mysql_conn
from persistence import temp_recorder

router = APIRouter(tags=["simulation"])


@router.get("/records/{project_id}")
async def list_project_records(project_id: int, limit: int = Query(default=100, ge=1, le=1000)):
    try:
        rows = await list_records(project_id=project_id, limit=limit)
        return {"projectId": project_id, "records": jsonable_encoder(rows)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to query records: {exc}")


@router.get("/record-series/{record_id}")
async def get_record_series_detail(
    record_id: int,
    state_limit: int = Query(default=5000, ge=1, le=200000),
    entity_limit: int = Query(default=50000, ge=1, le=500000),
    start_slot: int | None = Query(default=None, ge=0),
    slot_limit: int | None = Query(default=None, ge=1, le=5000),
):
    try:
        payload = await get_record_series(
            record_id=record_id,
            state_limit=state_limit,
            entity_limit=entity_limit,
            start_slot=start_slot,
            slot_limit=slot_limit,
        )
        return {"recordId": record_id, **jsonable_encoder(payload)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to query record series: {exc}")


@router.delete("/records/{record_id}")
async def delete_project_record(record_id: int):
    try:
        deleted = await delete_record(record_id=record_id)
        if deleted == 0:
            raise HTTPException(status_code=404, detail="Record not found")
        return {"recordId": record_id, "deleted": True}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to delete record: {exc}")


@router.delete("/records/project/{project_id}")
async def clear_project_records(project_id: int):
    try:
        deleted = await delete_records_by_project(project_id=project_id)
        return {"projectId": project_id, "deleted": int(deleted)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to clear records: {exc}")


@router.post("/record/{session_id}/save")
async def save_temp_record(session_id: str, status: str = "completed"):
    """保存临时记录到时序数据库"""
    record_id = await temp_recorder.save_session(session_id, record_status=status)
    if record_id is None:
        raise HTTPException(status_code=404, detail="Session not found or empty")
    return {"recordId": record_id, "saved": True}


@router.post("/record/{session_id}/discard")
async def discard_temp_record(session_id: str):
    """丢弃临时记录"""
    ok = await temp_recorder.discard_session(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"discarded": True}


@router.websocket("/ws/{project_id}")
async def simulation_ws(websocket: WebSocket, project_id: int):
    await websocket.accept()
    ground_stations: List[GroundStationBase] = []
    
    # 加载项目数据
    try:
        with get_mysql_conn() as conn:
            with conn.cursor() as cursor:
                project = fetch_project_by_id(cursor, project_id)
                if project:
                    cursor.execute(
                        """
                        SELECT id, project_id, name, latitude, longitude, altitude, created_at, updated_at
                        FROM ground_stations
                        WHERE project_id = %s
                        ORDER BY id DESC
                        """,
                        (project_id,),
                    )
                    ground_stations = [GroundStationBase(**row) for row in cursor.fetchall()]
    except Exception as exc:
        await websocket.send_json({
            "type": "error",
            "projectId": project_id,
            "message": f"Failed to load project from MySQL: {exc}",
        })
        await websocket.close(code=1011)
        return
    
    # 项目不存在
    if not project:
        await websocket.send_json({
            "type": "error",
            "projectId": project_id,
            "message": "Project not found",
        })
        await websocket.close(code=1008)
        return

    # 将 datetime 转为 ISO 字符串，匹配 ProjectBase 的 string 字段
    if isinstance(project, dict):
        for key in ("startTime", "endTime", "createdAt", "updatedAt"):
            if key in project and isinstance(project[key], datetime):
                project[key] = project[key].isoformat()

    project_model: ProjectBase = ProjectBase.model_validate(project)
    
    # 初始化仿真引擎
    engine = SimulatorEngine()
    session_id: str | None = None

    async def render_hook(state: dict):
        if session_id is not None:
            temp_recorder.append_state(session_id, state)
        await websocket.send_json(
            jsonable_encoder({"type": "state", "projectId": project_id, "state": state})
        )

    engine.set_render_hook(render_hook)
    
    # 传递整个项目数据，供引擎内部解析使用
    await engine.initialize(project_model, ground_stations)
    
    run_task = asyncio.create_task(engine.run())

    try:
        await websocket.send_json({
            "type": "connected",
            "projectId": project_id,
            "project": jsonable_encoder(project_model),
            "groundStations": jsonable_encoder(ground_stations),
        })
        while True:
            recv_task = asyncio.create_task(websocket.receive_json())
            done, _ = await asyncio.wait(
                {recv_task, run_task},
                return_when=asyncio.FIRST_COMPLETED,
            )

            if run_task in done:
                if not recv_task.done():
                    recv_task.cancel()
                    with suppress(asyncio.CancelledError):
                        await recv_task
                # 不发 DB，通知前端弹窗
                try:
                    await websocket.send_json({
                        "type": "simulation_ended",
                        "sessionId": session_id,
                    })
                except RuntimeError:
                    pass  # WebSocket 已关闭
                break

            msg = recv_task.result()
            action = msg.get("action")
            if action in {"play", "pause", "stop"}:
                # 首次 play 创建 temp session
                if action == "play" and session_id is None:
                    try:
                        session_id = temp_recorder.create_session(
                            project_id=project_id,
                            run_config=project_model.model_dump(),
                        )
                        await websocket.send_json({"type": "session_created", "sessionId": session_id})
                    except Exception as exc:
                        print(f"[Record] failed to create temp session: {exc}")
                await engine.input_queue.put({"action": action})

            if action == "stop":
                try:
                    await websocket.send_json({
                        "type": "simulation_ended",
                        "sessionId": session_id,
                    })
                except RuntimeError:
                    pass  # WebSocket 已关闭
                break
    except WebSocketDisconnect:
        pass
    finally:
        await engine.input_queue.put({"action": "stop"})
        try:
            await asyncio.wait_for(run_task, timeout=2.0)
        except asyncio.TimeoutError:
            run_task.cancel()
            with suppress(asyncio.CancelledError):
                await run_task
        except Exception:
            run_task.cancel()
