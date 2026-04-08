import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder

from core.simulation_engine import SimulatorEngine
from controller.project_controller import fetch_project_by_id, get_mysql_conn

router = APIRouter(tags=["simulation"])


@router.websocket("/ws/simulation/{project_id}")
async def simulation_ws(websocket: WebSocket, project_id: int):
    await websocket.accept()

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

    if not project:
        await websocket.send_json({
            "type": "error",
            "projectId": project_id,
            "message": "Project not found",
        })
        await websocket.close(code=1008)
        return

    project_payload = jsonable_encoder(project)

    engine = SimulatorEngine(target_hz=10.0)
    await engine.initialize({"project_id": project_id, "project": project})

    async def render_hook(state: dict):
        await websocket.send_json(
            jsonable_encoder({"type": "state", "projectId": project_id, "state": state})
        )

    engine.set_render_hook(render_hook)
    run_task = asyncio.create_task(engine.run())

    try:
        await websocket.send_json({"type": "ready", "projectId": project_id, "project": project_payload})
        while True:
            msg = await websocket.receive_json()
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
