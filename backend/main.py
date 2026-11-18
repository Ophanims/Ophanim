"""Local application with TimescaleDB records and a file-backed project catalog."""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from simulator.api import router, close_simulation_resources
from simulator.settings import SIMULATION_DATA_DIR
from persistence.record_repository import RecordRepository


@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.to_thread(SIMULATION_DATA_DIR.mkdir, parents=True, exist_ok=True)
    await asyncio.to_thread(RecordRepository().ensure_schema)
    try:
        yield
    finally:
        await close_simulation_resources()


app = FastAPI(title="OPHANIM API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(router)


@app.get("/health")
def health_check():
    return {"ok": True}
