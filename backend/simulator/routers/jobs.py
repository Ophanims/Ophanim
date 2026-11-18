"""Optional training and evaluation job HTTP boundary."""
import asyncio
from fastapi import APIRouter, HTTPException
from simulator.schemas.base import ApiResponse
from simulator.schemas.project import Project
from simulator.services.background_jobs import JobSnapshot, jobs

router = APIRouter(tags=["jobs"])


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
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc


@router.delete("/jobs/{job_id}", response_model=ApiResponse[JobSnapshot])
async def cancel_job(job_id: str):
    try:
        return ApiResponse(status="success", data=await asyncio.to_thread(jobs.cancel_job, job_id))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc
