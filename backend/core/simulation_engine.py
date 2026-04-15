import asyncio
import math
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from algorithm.algo_manager import ALGO_MANAGER
from entity.world import WORLD, World
from backend.topology.link import Link
from util.const import DEFAULT_SIMULATION_TIMESLOT
from util.time_utils import parse_datetime, to_iso_string, to_skyfield_time

from entity.entity import Entity
from status.engine_status import EngineStatus
from controller.project_controller import GroundStationBase, ProjectBase

class SimulationState(BaseModel):
    """全局快照，用于前端渲染"""
    timestamp: float = 0.0
    slot_count: int = 0
    timeslot: float = 0.0
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    now: Optional[str] = None
    maximum_slot: Optional[int] = None
    entities: List[Dict[str, Any]] = Field(default_factory=list)  # 每个实体的快照数据列表
    links: List[Dict[str, Any]] = Field(default_factory=list)     # 每个链路的快照数据列表

class SimulatorEngine:
    def __init__(self):
        self.hz = 50
        self.dt = 1.0 / self.hz

        self.status = EngineStatus.IDLE
        self.state = SimulationState()
        
        self.world = WORLD  # 整合环境、实体和链路的容器

        # 逻辑时间配置（由 project.timeSlot/startTime/endTime 驱动）
        self.SLOT: float = 0.0
        self.START_TIME: Optional[datetime] = None
        self.END_TIME: Optional[datetime] = None
        self.MAX_SLOT: Optional[int] = None
        self.SEED: Optional[int] = None
        
        # 外部钩子（由 FastAPI 注入）
        self.on_render_hook = None 
        self.input_queue = asyncio.Queue()

    def set_render_hook(self, callback):
        """注入 WebSocket 发送逻辑"""
        self.on_render_hook = callback

    def _collect_entity_snapshots(self, entities: List[Entity]) -> List[Dict[str, Any]]:
        snapshots: List[Dict[str, Any]] = []
        for e in entities:
            data = e.serialize()
            snapshots.append(data)
        return snapshots

    def _collect_link_snapshots(self, links: List[Link]) -> List[Dict[str, Any]]:
        snapshots: List[Dict[str, Any]] = []
        for l in links:
            if l.status:  # 仅记录连通的链路
                data = l.serialize()
                snapshots.append(data)
        return snapshots

    # --- 生命周期控制 ---
    async def initialize(self, project: ProjectBase, ground_stations: List[GroundStationBase]):
        print("[Engine] Initializing components...")
        WORLD = World()  # 重置全局环境实例
        self.world = WORLD

        # timeSlot 作为逻辑步长（秒）
        self.SLOT = project.timeSlot if project.timeSlot and project.timeSlot > 0 else DEFAULT_SIMULATION_TIMESLOT
        self.SEED = project.seed if project.seed else None
            
        # startTime/endTime 作为逻辑时间范围    
        T_START = parse_datetime(project.startTime) if project.startTime else None
        if T_END is None or T_END < self.START_TIME:
            self.END_TIME = self.START_TIME + timedelta(days=1)
        else:
            self.END_TIME = T_END
            
        T_END = parse_datetime(project.endTime) if project.endTime else None
        if T_START is None:
            self.START_TIME = datetime.now(timezone.utc)
        else:
            self.START_TIME = T_START

        # 这里就安全了
        self.state.start_time = to_iso_string(self.START_TIME)
        self.state.end_time = to_iso_string(self.END_TIME)
            
        # 计算总步数（如果 endTime 可用）
        SPAN = (self.END_TIME - self.START_TIME).total_seconds()
        self.MAX_SLOT = max(0, math.floor(SPAN / self.SLOT)) + 1
        
        self.world.setup(pjc_base=project, gs_base=ground_stations)
            
        self.state.slot_count = 0
        self.state.timestamp = 0.0
        self.state.timeslot = self.SLOT
        self.state.start_time = to_iso_string(self.START_TIME)
        self.state.end_time = to_iso_string(self.END_TIME)
        self.state.now = self.state.start_time
        self.state.maximum_slot = self.MAX_SLOT
        self.state.entities = self._collect_entity_snapshots(self.world.entities)
        self.state.links = self._collect_link_snapshots(self.world.links)
        self.status = EngineStatus.IDLE
        
        # if self.on_render_hook:
        #     # 执行回调，将 state 发送到 WebSocket
        #     await self.on_render_hook(self.state.model_dump())

    async def _handle_outside_commannd(self):
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
        
        while self.status != EngineStatus.STOPPED and self.state.slot_count < self.MAX_SLOT:
            start_time = time.perf_counter()

            # 1. 处理输入
            await self._handle_outside_commannd()

            # 2. 逻辑更新 (仅在 RUNNING 状态)
            if self.status == EngineStatus.RUNNING:
                # endTime 到达后自动停止
                if self.MAX_SLOT is not None and self.state.slot_count >= self.MAX_SLOT:
                    self.status = EngineStatus.STOPPED
                    continue

                now = self.START_TIME + timedelta(seconds=self.state.slot_count * self.SLOT)
                skyfield_time = to_skyfield_time(now)
                
                self.world.tick(current_time=skyfield_time, current_slot=self.state.slot_count)
                
                self.state.timestamp += self.SLOT
                self.state.slot_count += 1
                self.state.now = to_iso_string(now)
                self.state.entities = self._collect_entity_snapshots(self.world.entities)
                self.state.links = self._collect_link_snapshots(self.world.links)

                # 3. 数据导出/渲染
                if self.on_render_hook:
                    # 执行回调，将 state 发送到 WebSocket
                    await self.on_render_hook(self.state.model_dump())

            # 4. 频率控制
            elapsed = time.perf_counter() - start_time
            sleep_time = max(0, self.dt - elapsed)
            await asyncio.sleep(sleep_time)

        print("[Engine] Loop terminated.")