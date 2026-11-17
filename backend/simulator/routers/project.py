"""Project HTTP boundary: validated contracts and application services only."""
import asyncio
from fastapi import APIRouter, HTTPException
from simulator.schemas.base import ApiResponse
from simulator.schemas.project import Project
from simulator.services.project_repository import ProjectRepository
from simulator.services.project_service import detect_update

router = APIRouter(prefix="/projects", tags=["projects"])
repository = ProjectRepository()


@router.get("", response_model=ApiResponse[list[Project]], operation_id="list_projects")
async def list_projects():
    return ApiResponse(status="success", data=await asyncio.to_thread(repository.list_projects))


@router.post("/detect", response_model=ApiResponse[Project], operation_id="detect_project")
async def detect_project(project: Project):
    try:
        return ApiResponse(status="success", data=await asyncio.to_thread(detect_update, project))
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("", response_model=ApiResponse[Project], operation_id="save_project")
async def save_project(project: Project):
    try:
        project = await asyncio.to_thread(detect_update, project)
        return ApiResponse(status="success", data=await asyncio.to_thread(repository.save_project, project))
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{project_id}", response_model=ApiResponse[Project], operation_id="get_project")
async def get_project(project_id: str):
    try:
        return ApiResponse(status="success", data=await asyncio.to_thread(repository.get_project, project_id))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.delete("/{project_id}", response_model=ApiResponse[str], operation_id="delete_project")
async def delete_project(project_id: str):
    try:
        await asyncio.to_thread(repository.delete_project, project_id)
        return ApiResponse(status="success", data="deleted")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
