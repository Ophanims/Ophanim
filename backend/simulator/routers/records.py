import asyncio
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from persistence.record_repository import RecordRepository
from simulator.schemas.base import ApiResponse
from simulator.services.record_contracts import AnalysisWindow, EntityType, RecordSnapshot, RecordWindow
from simulator.services import session_records

router = APIRouter(prefix="/records", tags=["records"])


@router.get("", response_model=ApiResponse[list[RecordSnapshot]])
async def list_records(limit: int = Query(50, ge=1, le=200), project_id: str | None = None):
    return ApiResponse(status="success", data=await asyncio.to_thread(session_records.list_records, limit, project_id))


@router.get("/{record_id}", response_model=ApiResponse[RecordWindow])
async def get_record(record_id: str, start_frame: int = Query(0, ge=0), frame_limit: int = Query(600, ge=1, le=600)):
    try:
        return ApiResponse(status="success", data=await asyncio.to_thread(session_records.get_record_window, record_id, start_frame, frame_limit))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Record not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{record_id}/download")
async def download_record(record_id: str):
    try:
        record = await asyncio.to_thread(session_records.get_record, record_id)
        return StreamingResponse(session_records.iter_record_lines(record_id), media_type="application/x-ndjson",
            headers={"Content-Disposition": f'attachment; filename="{record.record_id}.ndjson"'})
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Record not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{record_id}/analysis", response_model=ApiResponse[AnalysisWindow])
async def get_record_analysis(record_id: str, entity_type: EntityType, id: str | None = None,
                              start_frame: int = Query(0, ge=0), frame_limit: int = Query(600, ge=1, le=600),
                              point_limit: int = Query(5000, ge=1, le=10000), start_point: int = Query(0, ge=0)):
    try:
        window = await asyncio.to_thread(RecordRepository().get_analysis, record_id, entity_type, id,
                                         start_frame, start_frame + frame_limit, point_limit, start_point)
        return ApiResponse(status="success", data=window)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Record not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.delete("/{record_id}", response_model=ApiResponse[str])
async def delete_record(record_id: str):
    try:
        await asyncio.to_thread(session_records.delete_record, record_id)
        return ApiResponse(status="success", data="deleted")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Record not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
