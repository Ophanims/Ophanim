import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controller.project_controller import ensure_projects_table, router as project_router
from controller.simulation_controller import router as simulation_router

app = FastAPI(title="OPHANIM API", version="0.1.0")

# 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 或前端域名
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_init_db():
    ensure_projects_table()


@app.get("/health")
def health_check():
    return {"ok": True}


app.include_router(project_router)
app.include_router(simulation_router)

