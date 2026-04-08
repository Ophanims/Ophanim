import asyncio
from contextlib import suppress
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder

from core.simulation_engine import SimulatorEngine
from controller.record_controller import create_record, append_record_state, finish_record, get_record_series, list_records
from controller.project_controller import ProjectBase, fetch_project_by_id, get_mysql_conn

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
):
    try:
        payload = await get_record_series(
            record_id=record_id,
            state_limit=state_limit,
            entity_limit=entity_limit,
        )
        return {"recordId": record_id, **jsonable_encoder(payload)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to query record series: {exc}")


@router.websocket("/ws/{project_id}")
async def simulation_ws(websocket: WebSocket, project_id: int):
    await websocket.accept()
    
    # 加载项目数据
    try:
        with get_mysql_conn() as conn:
            with conn.cursor() as cursor:
                project = fetch_project_by_id(cursor, project_id)
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
    record_id: int | None = None
    record_status = "stopped"
    record_error: str | None = None

    try:
        record_id = await create_record(project_id=project_id, run_config=project_model.model_dump())
    except Exception as exc:
        # 记录创建失败不阻断仿真，避免影响在线播放。
        print(f"[Record] failed to create record for project {project_id}: {exc}")

    async def render_hook(state: dict):
        if record_id is not None:
            try:
                await append_record_state(record_id=record_id, project_id=project_id, state=state)
            except Exception as exc:
                print(f"[Record] failed to append state for record {record_id}: {exc}")
        await websocket.send_json(
            jsonable_encoder({"type": "state", "projectId": project_id, "state": state})
        )

    engine.set_render_hook(render_hook)
    
    # 传递整个项目数据，供引擎内部解析使用
    await engine.initialize(project_model)
    
    run_task = asyncio.create_task(engine.run())

    try:
        await websocket.send_json({
            "type": "connected",
            "projectId": project_id,
            "recordId": record_id,
            "project": jsonable_encoder(project_model)
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

                exc = run_task.exception()
                if exc is not None:
                    record_status = "failed"
                    record_error = str(exc)
                    await websocket.send_json({
                        "type": "error",
                        "projectId": project_id,
                        "message": f"Simulation engine crashed: {exc}",
                    })
                elif engine.MAX_SLOT is not None and engine.state.slot_count >= engine.MAX_SLOT:
                    record_status = "completed"
                break

            msg = recv_task.result()
            action = msg.get("action")
            if action in {"play", "pause", "stop"}:
                await engine.input_queue.put({"action": action})

            if action == "stop":
                record_status = "stopped"
                break
    except WebSocketDisconnect:
        record_status = "stopped"
    finally:
        await engine.input_queue.put({"action": "stop"})
        try:
            await asyncio.wait_for(run_task, timeout=2.0)
        except asyncio.TimeoutError:
            run_task.cancel()
            with suppress(asyncio.CancelledError):
                await run_task
            if record_status not in {"failed", "completed"}:
                record_status = "stopped"
        except Exception as exc:
            run_task.cancel()
            if record_status != "failed":
                record_status = "failed"
                record_error = f"run task cancelled on shutdown: {exc}"

        if run_task.done() and not run_task.cancelled():
            exc = run_task.exception()
            if exc is not None:
                record_status = "failed"
                record_error = str(exc)

        if record_id is not None:
            try:
                await finish_record(record_id=record_id, status=record_status, error_message=record_error)
            except Exception as exc:
                print(f"[Record] failed to finish record {record_id}: {exc}")
