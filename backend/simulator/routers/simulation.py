"""One connection, one session, one writer; no shared world or clock."""
import asyncio
import logging
from contextlib import suppress
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from simulator.contracts import ControlMessage, ErrorMessage, StateMessage, StatusMessage
from simulator.core.session import SimulationSession
from simulator.services.project_service import detect_update
from simulator.services.session_records import SessionRecord

router = APIRouter(tags=["simulation"])
logger = logging.getLogger(__name__)


@router.websocket("/simulation/ws")
async def simulation_ws(websocket: WebSocket):
    await websocket.accept()
    session = None
    record = None
    record_status = "disconnected"
    is_running = False
    await websocket.send_json(StatusMessage(status="connected").serialize())
    try:
        while True:
            try:
                raw = await asyncio.wait_for(websocket.receive_json(), timeout=0.1)
            except asyncio.TimeoutError:
                if not is_running or session is None:
                    continue
                state = await asyncio.to_thread(session.step)
                await asyncio.to_thread(record.append_state, state)
                await websocket.send_json(StateMessage(state=state).serialize())
                if session.is_completed:
                    is_running = False
                    record_status = "completed"
                    await asyncio.to_thread(record.close, record_status)
                    await websocket.send_json(StatusMessage(status="completed").serialize())
                continue
            try:
                command = ControlMessage.model_validate(raw)
                if command.action == "init":
                    if command.payload is None:
                        raise ValueError("init requires payload")
                    if session is not None:
                        raise ValueError("Close the current session before initializing another")
                    project = await asyncio.to_thread(detect_update, command.payload)
                    project.algorithm = command.algorithm if "algorithm" in command.model_fields_set else project.algorithm
                    session = await asyncio.to_thread(SimulationSession, project, project.algorithm)
                    record = await asyncio.to_thread(SessionRecord, project, project.algorithm)
                    state = session.snapshot()
                    await asyncio.to_thread(record.append_state, state)
                    await websocket.send_json(StateMessage(state=state).serialize())
                    await websocket.send_json(StatusMessage(status="ready").serialize())
                elif command.action == "play":
                    if session is None or session.is_completed:
                        raise ValueError("Initialize an active session before play")
                    is_running = True
                    await websocket.send_json(StatusMessage(status="running").serialize())
                elif command.action == "pause":
                    is_running = False
                    await websocket.send_json(StatusMessage(status="paused").serialize())
                elif command.action == "stop":
                    if record_status != "completed":
                        record_status = "stopped"
                    await websocket.send_json(StatusMessage(status="stopped").serialize())
                    break
            except (ValidationError, ValueError, FileNotFoundError) as exc:
                await websocket.send_json(ErrorMessage(message=str(exc)).serialize())
            except ImportError:
                logger.exception("Optional algorithm dependencies unavailable")
                await websocket.send_json(ErrorMessage(message="Install backend/requirements-ml.txt to use this algorithm").serialize())
    except WebSocketDisconnect:
        logger.info("Simulation session disconnected")
    except Exception:
        record_status = "failed"
        logger.exception("Simulation session failed")
        if websocket.client_state.name == "CONNECTED":
            await websocket.send_json(ErrorMessage(message="Simulation failed; see server logs").serialize())
    finally:
        if record is not None:
            await asyncio.to_thread(record.close, record_status)
        if session is not None:
            await asyncio.to_thread(session.close)
        if websocket.client_state.name == "CONNECTED" and websocket.application_state.name == "CONNECTED":
            with suppress(RuntimeError, WebSocketDisconnect):
                await websocket.close()
