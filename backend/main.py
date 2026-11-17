import os
import sys
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from persistence.schema_bootstrap import ensure_projects_table, ensure_record_schema
from simulator.services.project_migration import migrate_ophanim_projects
from simulator.services.record_migration import migrate_ophanim_records

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
            await asyncio.to_thread(ensure_projects_table)
            await asyncio.to_thread(migrate_ophanim_projects)
            await ensure_record_schema()
            await asyncio.to_thread(migrate_ophanim_records)
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




# One API and lifecycle for every simulation strategy.
from simulator.api import router as simulation_router, close_simulation_resources
app.include_router(simulation_router)
app.add_event_handler("shutdown", close_simulation_resources)
