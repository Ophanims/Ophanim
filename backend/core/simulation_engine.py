import asyncio
import math
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from algorithm.algo_manager import ALGO_MANAGER
from core.simulation_clock import CLOCK
from entity.mission import Mission
from entity.world import WORLD, World
from topology.link import Link
from util.const import DEFAULT_SIMULATION_TIMESLOT
from util.time_utils import parse_datetime, to_iso_string, to_skyfield_time

from entity.entity import Entity
from status.engine_status import EngineStatus
from controller.project_controller import GroundStationBase, ProjectBase

class SimulationState(BaseModel):
    """全局快照，用于前端渲染"""
    clock: Dict[str, Any] = Field(default_factory=dict)  # 当前时间、时间槽等信息   
    entities: List[Dict[str, Any]] = Field(default_factory=list)  # 每个实体的快照数据列表
    links: List[Dict[str, Any]] = Field(default_factory=list)     # 每个链路的快照数据列表
    missions: List[Dict[str, Any]] = Field(default_factory=list)   # 每个任务的快照数据列表

class SimulatorEngine:
    def __init__(self):
        self.hz = 50
        self.dt = 1.0 / self.hz

        self.status = EngineStatus.IDLE
        self.state = SimulationState()
        
        self.world = WORLD  # 整合环境、实体和链路的容器
        self.clock = CLOCK  # 统一的模拟器时钟实例
        
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

    def _collect_mission_snapshots(self, missions: List[Mission]) -> List[Dict[str, Any]]:
        snapshots: List[Dict[str, Any]] = []
        for m in missions:
            data = m.serialize()
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
        
        self.world = WORLD
        self.world.setup(project, ground_stations)

        self.clock = CLOCK
        self.clock.setup(project)
            
        self.state.clock = CLOCK.snapshot()
        
        self.state.entities = self._collect_entity_snapshots(self.world.entities)
        self.state.links = self._collect_link_snapshots(self.world.links)
        self.state.missions = self._collect_mission_snapshots(self.world.missions)
        
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
        
        while self.status != EngineStatus.STOPPED and self.clock.current_slot < self.clock.END_SLOT:
            start_time = time.perf_counter()

            # 1. 处理输入
            await self._handle_outside_commannd()

            # 2. 逻辑更新 (仅在 RUNNING 状态)
            if self.status == EngineStatus.RUNNING:
                # endTime 到达后自动停止
                if self.clock.END_SLOT is not None and self.clock.current_slot >= self.clock.END_SLOT:
                    self.status = EngineStatus.STOPPED
                    continue
                self.clock.tick()  # 推进一个时间槽，更新 current_time 和 current_slot
                self.world.tick()

                self.state.clock = CLOCK.snapshot()
                
                self.state.entities = self._collect_entity_snapshots(self.world.entities)
                self.state.links = self._collect_link_snapshots(self.world.links)
                self.state.missions = self._collect_mission_snapshots(self.world.missions)

                # 3. 数据导出/渲染
                if self.on_render_hook:
                    # 执行回调，将 state 发送到 WebSocket
                    await self.on_render_hook(self.state.model_dump())

            # 4. 频率控制
            elapsed = time.perf_counter() - start_time
            sleep_time = max(0, self.dt - elapsed)
            await asyncio.sleep(sleep_time)

        print("[Engine] Loop terminated.")