import os
import sys
import asyncio
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from controller.project_controller import ensure_projects_table, router as project_router
from controller.record_controller import ensure_record_schema
from controller.simulation_controller import router as simulation_router

app = FastAPI(title="OPHANIM API", version="0.1.0")

# 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 或前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_init_db():
    """启动时初始化数据库，带重试机制"""
    max_retries = 15
    retry_delay = 2  # 秒

    for attempt in range(max_retries):
        try:
            ensure_projects_table()
            try:
                await ensure_record_schema()
            except Exception as rec_err:
                print(f"Timescale schema init skipped: {rec_err}")
            print("Database connected and initialized successfully")
            break
        except Exception as e:
            print(f"Database connection attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
            else:
                print("Failed to connect to database after all retries")
                raise


@app.get("/health")
def health_check():
    return {"ok": True}


app.include_router(project_router, prefix="/api/projects", tags=["projects"])
app.include_router(simulation_router, prefix="/api/simulation", tags=["simulation"])

