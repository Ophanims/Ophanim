"""The application's only HTTP and WebSocket route registry."""
import asyncio
from fastapi import APIRouter
from simulator.routers import cache, project, simulation, records
from simulator.services.background_jobs import jobs

router = APIRouter(prefix="/api")
router.include_router(project.router)
router.include_router(cache.router)
router.include_router(records.router)
router.include_router(simulation.router)


async def close_simulation_resources():
    await asyncio.to_thread(jobs.close)
