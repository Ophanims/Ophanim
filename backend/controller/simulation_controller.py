import asyncio
from contextlib import suppress
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder

from core.simulation_engine import SimulatorEngine
from controller.project_controller import ProjectBase, fetch_project_by_id, get_mysql_conn

router = APIRouter(tags=["simulation"])


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

    async def render_hook(state: dict):
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
                    await websocket.send_json({
                        "type": "error",
                        "projectId": project_id,
                        "message": f"Simulation engine crashed: {exc}",
                    })
                break

            msg = recv_task.result()
            action = msg.get("action")
            if action in {"play", "pause", "stop"}:
                await engine.input_queue.put({"action": action})

            if action == "stop":
                break
    except WebSocketDisconnect:
        pass
    finally:
        await engine.input_queue.put({"action": "stop"})
        try:
            await asyncio.wait_for(run_task, timeout=2.0)
        except Exception:
            run_task.cancel()
