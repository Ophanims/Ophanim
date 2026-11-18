"""One WebSocket writer; simulation and durable recording run independently."""
import asyncio
import logging
from contextlib import suppress
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from simulator.contracts import ControlMessage, ErrorMessage, StateMessage, StatusMessage
from simulator.core.session import SimulationSession
from simulator.services.project_service import detect_update
from simulator.services.realtime_runner import RealtimeRunner
from simulator.services.session_records import SessionRecord

router = APIRouter(tags=["simulation"])
logger = logging.getLogger(__name__)


@router.websocket("/simulation/ws")
async def simulation_ws(websocket: WebSocket):
    await websocket.accept()
    session = record = runner = None
    record_status = "disconnected"
    receive_task = update_task = None
    last_frame = -1
    completed_sent = False
    await websocket.send_json(StatusMessage(status="connected").serialize())
    try:
        receive_task = asyncio.create_task(websocket.receive_json())
        while True:
            pending = [receive_task] + ([update_task] if update_task else [])
            done, _ = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
            if receive_task in done:
                raw = receive_task.result()
                receive_task = asyncio.create_task(websocket.receive_json())
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
                        runner = RealtimeRunner(session, record)
                        update_task = asyncio.create_task(runner.changed.wait())
                        last_frame = state.frame_counter
                        await websocket.send_json(StateMessage(state=state).serialize())
                        await websocket.send_json(StatusMessage(status="ready").serialize())
                    elif command.action == "play":
                        if runner is None:
                            raise ValueError("Initialize an active session before play")
                        runner.play()
                        await websocket.send_json(StatusMessage(status="running").serialize())
                    elif command.action == "pause":
                        if runner is not None:
                            runner.pause()
                        await websocket.send_json(StatusMessage(status="paused").serialize())
                    elif command.action == "stop":
                        if runner is not None:
                            await runner.stop()
                        record_status = "completed" if runner and runner.completed else "stopped"
                        if record is not None:
                            await asyncio.to_thread(record.close, record_status)
                        await websocket.send_json(StatusMessage(status="stopped").serialize())
                        break
                except (ValidationError, ValueError, FileNotFoundError) as exc:
                    await websocket.send_json(ErrorMessage(message=str(exc)).serialize())
                except ImportError:
                    logger.exception("Optional algorithm dependencies unavailable")
                    await websocket.send_json(ErrorMessage(message="Install backend/requirements-ml.txt to use this algorithm").serialize())
            if update_task is not None and update_task in done:
                runner.changed.clear()
                state = runner.latest_state
                if state.frame_counter != last_frame:
                    await websocket.send_json(StateMessage(state=state).serialize())
                    last_frame = state.frame_counter
                if runner.error is not None:
                    record_status = "failed"
                    await websocket.send_json(ErrorMessage(message="Simulation or recording failed; see server logs").serialize())
                    break
                if runner.completed and not completed_sent:
                    record_status = "completed"
                    completed_sent = True
                    await websocket.send_json(StatusMessage(status="completed").serialize())
                update_task = None if runner.completed else asyncio.create_task(runner.changed.wait())
    except WebSocketDisconnect:
        logger.info("Simulation session disconnected")
    except Exception:
        record_status = "failed"
        logger.exception("Simulation session failed")
        if websocket.client_state.name == "CONNECTED":
            with suppress(RuntimeError, WebSocketDisconnect):
                await websocket.send_json(ErrorMessage(message="Simulation failed; see server logs").serialize())
    finally:
        for task in (receive_task, update_task):
            if task is not None:
                task.cancel()
        await asyncio.gather(*(task for task in (receive_task, update_task) if task is not None), return_exceptions=True)
        try:
            if runner is not None:
                await runner.stop()
                if runner.completed:
                    record_status = "completed"
                elif runner.error is not None:
                    record_status = "failed"
            if record is not None:
                await asyncio.to_thread(record.close, record_status)
        except Exception:
            logger.exception("Record finalization failed; recovery journal retained")
        finally:
            if session is not None:
                await asyncio.to_thread(session.close)
            if websocket.client_state.name == "CONNECTED" and websocket.application_state.name == "CONNECTED":
                with suppress(RuntimeError, WebSocketDisconnect):
                    await websocket.close()
