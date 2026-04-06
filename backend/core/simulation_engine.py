import asyncio
import time
import json
from enum import Enum
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

# --- 1. 状态定义 ---
class EngineStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"

class SimulationState(BaseModel):
    """全局快照，用于前端渲染"""
    timestamp: float = 0.0
    tick_count: int = 0
    entities: Dict[str, Any] = {}
    metrics: Dict[str, Any] = {}

# --- 2. 核心组件基类 ---
class SimComponent:
    """所有仿真逻辑（如轨道、能量、计算任务）必须继承此类"""
    def setup(self, config: Any): pass
    def update(self, dt: float, state: SimulationState): pass

# --- 3. 仿真引擎核心 ---
class SimulatorEngine:
    def __init__(self, target_hz: float = 10.0):
        self.hz = target_hz
        self.dt = 1.0 / target_hz
        
        self.status = EngineStatus.IDLE
        self.state = SimulationState()
        self.components: List[SimComponent] = []
        
        # 外部钩子（由 FastAPI 注入）
        self.on_render_hook = None 
        self.input_queue = asyncio.Queue()

    def add_component(self, component: SimComponent):
        self.components.append(component)

    def set_render_hook(self, callback):
        """注入 WebSocket 发送逻辑"""
        self.on_render_hook = callback

    # --- 生命周期控制 ---
    async def initialize(self, config: Any):
        print("[Engine] Initializing components...")
        for comp in self.components:
            comp.setup(config)
        self.state.timestamp = 0.0
        self.state.tick_count = 0
        self.status = EngineStatus.IDLE

    async def _handle_inputs(self):
        """非阻塞处理外部指令"""
        while not self.input_queue.empty():
            cmd = await self.input_queue.get()
            await self._process_command(cmd)

    async def _process_command(self, cmd: dict):
        action = cmd.get("action")
        if action == "play": self.status = EngineStatus.RUNNING
        elif action == "pause": self.status = EngineStatus.PAUSED
        elif action == "stop": self.status = EngineStatus.STOPPED

    # --- 主循环 ---
    async def run(self):
        print(f"[Engine] Main loop started at {self.hz}Hz")
        
        while self.status != EngineStatus.STOPPED:
            start_time = time.perf_counter()

            # 1. 处理输入
            await self._handle_inputs()

            # 2. 逻辑更新 (仅在 RUNNING 状态)
            if self.status == EngineStatus.RUNNING:
                for comp in self.components:
                    # 每个组件根据当前的 dt 更新 self.state
                    comp.update(self.dt, self.state)
                
                self.state.timestamp += self.dt
                self.state.tick_count += 1

                # 3. 数据导出/渲染
                if self.on_render_hook:
                    # 执行回调，将 state 发送到 WebSocket
                    await self.on_render_hook(self.state.model_dump())

            # 4. 频率控制
            elapsed = time.perf_counter() - start_time
            sleep_time = max(0, self.dt - elapsed)
            await asyncio.sleep(sleep_time)

        print("[Engine] Loop terminated.")