import asyncio
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from simulator.schemas.base import ApiResponse
from simulator.services.session_records import RecordSnapshot, RecordWindow, get_record_window, record_path

router = APIRouter(prefix="/records", tags=["records"])


@router.get("", response_model=ApiResponse[list[RecordSnapshot]])
async def list_records(limit: int = Query(50, ge=1, le=200)):
    from simulator.services import session_records
    return ApiResponse(status="success", data=await asyncio.to_thread(session_records.list_records, limit))


@router.get("/{record_id}", response_model=ApiResponse[RecordWindow])
async def get_record(record_id: str, start_frame: int = Query(0, ge=0), frame_limit: int = Query(600, ge=1, le=600)):
    try:
        return ApiResponse(status="success", data=await asyncio.to_thread(get_record_window, record_id, start_frame, frame_limit))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Record not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{record_id}/download")
async def download_record(record_id: str):
    try:
        path = record_path(record_id, "ndjson")
        if not path.exists():
            raise HTTPException(status_code=404, detail="Record not found")
        return FileResponse(path, filename=f"{record_id}.ndjson", media_type="application/x-ndjson")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.delete("/{record_id}", response_model=ApiResponse[str])
async def delete_record(record_id: str):
    from simulator.services import session_records
    try:
        await asyncio.to_thread(session_records.delete_record, record_id)
        return ApiResponse(status="success", data="deleted")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Record not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
