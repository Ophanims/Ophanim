"""Derived data and optional ML job HTTP boundary."""
import asyncio
from fastapi import APIRouter, HTTPException
from simulator.schemas.base import ApiResponse
from simulator.schemas.project import Project
from simulator.services import cache_service
from simulator.services.background_jobs import JobSnapshot, jobs

router = APIRouter(tags=["cache"])


@router.get("/cache/size", response_model=ApiResponse[int])
async def get_cache_size():
    return ApiResponse(status="success", data=await asyncio.to_thread(cache_service.get_cache_folder_size))


@router.post("/cache/clear", response_model=ApiResponse[str])
async def clear_cache():
    await asyncio.to_thread(cache_service.clear_cache_folder)
    return ApiResponse(status="success", data="cache cleared")


@router.post("/cache/check", response_model=ApiResponse[dict[str, bool]])
async def check_cache(project: Project):
    return ApiResponse(status="success", data=await asyncio.to_thread(cache_service.check_all_cache_integrity, project))


@router.post("/cache/initial", response_model=ApiResponse[str])
async def initial_cache(project: Project):
    try:
        await asyncio.to_thread(cache_service.initial_cache_setup, project)
        return ApiResponse(status="success", data="cache initialized")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/jobs/{job_type}", response_model=ApiResponse[JobSnapshot])
async def start_job(job_type: str, project: Project):
    if job_type not in {"train", "auto_test"}:
        raise HTTPException(status_code=404, detail="Unknown job type")
    try:
        return ApiResponse(status="success", data=jobs.start_job(project, job_type))
    except ImportError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/jobs/{job_id}", response_model=ApiResponse[JobSnapshot])
async def get_job(job_id: str):
    try:
        return ApiResponse(status="success", data=jobs.snapshot(job_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc


@router.delete("/jobs/{job_id}", response_model=ApiResponse[JobSnapshot])
async def cancel_job(job_id: str):
    try:
        return ApiResponse(status="success", data=await asyncio.to_thread(jobs.cancel_job, job_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc
