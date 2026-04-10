import asyncio
import math
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from entity.link import Link
from entity.eth import Earth
from entity.sun import Sun
from util.gs_generator import generate_stations
from util.const import DEFAULT_ALTITUDE, DEFAULT_CONSTELLATION_SIZE, DEFAULT_INCLINATION, DEFAULT_PHASE_FACTOR, DEFAULT_PLANE_COUNT, DEFAULT_SIMULATION_TIMESLOT
from util.sat_generator import generate_constellation
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
        self.entities: List[Entity] = []
        self.links: List[Link] = []

        # 逻辑时间配置（由 project.timeSlot/startTime/endTime 驱动）
        self.SLOT: float = 0.0
        self.START_TIME: Optional[datetime] = None
        self.END_TIME: Optional[datetime] = None
        self.MAX_SLOT: Optional[int] = None
        
        # 外部钩子（由 FastAPI 注入）
        self.on_render_hook = None 
        self.input_queue = asyncio.Queue()

    # def add_entity(self, entity: Entity):
    #     self.entities.append(entity)

    def set_render_hook(self, callback):
        """注入 WebSocket 发送逻辑"""
        self.on_render_hook = callback

    def _collect_entity_snapshots(self) -> List[Dict[str, Any]]:
        snapshots: List[Dict[str, Any]] = []
        for e in self.entities:
            data = e.serialize()
            snapshots.append(data)
        return snapshots

    def _collect_link_snapshots(self) -> List[Dict[str, Any]]:
        snapshots: List[Dict[str, Any]] = []
        for l in self.links:
            data = l.serialize()
            snapshots.append(data)
        return snapshots

    def _collect_entity_snapshots(self) -> List[Dict[str, Any]]:
        snapshots: List[Dict[str, Any]] = []
        for e in self.entities:
            data = e.serialize()
            snapshots.append(data)
        return snapshots

    # --- 生命周期控制 ---
    async def initialize(self, project: ProjectBase, ground_stations: List[GroundStationBase]):
        print("[Engine] Initializing components...")
        self.entities.clear()

        # timeSlot 作为逻辑步长（秒）
        self.SLOT = project.timeSlot if project.timeSlot and project.timeSlot > 0 else DEFAULT_SIMULATION_TIMESLOT
            
        # startTime/endTime 作为逻辑时间范围
        T_START = parse_datetime(project.startTime) if project.startTime else None
        T_END = parse_datetime(project.endTime) if project.endTime else None
        if T_START is None:
            self.START_TIME = datetime.now(timezone.utc)
        else:
            self.START_TIME = T_START
            
        if T_END is None or T_END < self.START_TIME:
            self.END_TIME = self.START_TIME + timedelta(days=1)
        else:
            self.END_TIME = T_END

        # 这里就安全了
        self.state.start_time = to_iso_string(self.START_TIME)
        self.state.end_time = to_iso_string(self.END_TIME)
            
        # 计算总步数（如果 endTime 可用）
        SPAN = (self.END_TIME - self.START_TIME).total_seconds()
        self.MAX_SLOT = max(0, math.floor(SPAN / self.SLOT)) + 1
        
        # 根据项目数据创建实体
        ALT = project.altitude if project.altitude and project.altitude > 0 else DEFAULT_ALTITUDE
        INC = project.inclination if project.inclination and 0 <= project.inclination <= 180 else DEFAULT_INCLINATION
        CON_SIZE = project.constellationSize if project.constellationSize else DEFAULT_CONSTELLATION_SIZE
        P_NUM = project.planeCount if project.planeCount else DEFAULT_PLANE_COUNT
        PF = project.phaseFactor if project.phaseFactor else DEFAULT_PHASE_FACTOR
        
        satellites = generate_constellation(alt=ALT, inc=INC, P=P_NUM, T=CON_SIZE, F=PF)
        stations = generate_stations(gs_models=ground_stations)
        
        sun = Sun()
        self.entities.append(sun)  # 添加太阳实体
        
        earth = Earth()
        self.entities.append(earth) # 添加地球实体
        
        nodes: List[Entity] = satellites + stations
        
        for sat in satellites:
            self.entities.append(sat)
        
        for station in stations:
            self.entities.append(station)
            

        # 调用每个组件的 setup 方法，传入整个项目数据
        for e in self.entities:
            e.setup(project)
            
        # 根据实体列表生成链路（全连接，后续可优化为基于距离或其他规则）
        for u in nodes:
            for v in nodes:
                if u != v:
                    l = Link(src=u, dst=v)
                    l.setup(project)
                    self.links.append(l)
                    
            
        self.state.timestamp = 0.0
        self.state.slot_count = 0
        self.state.timeslot = self.SLOT
        self.state.start_time = to_iso_string(self.START_TIME)
        self.state.end_time = to_iso_string(self.END_TIME)
        self.state.now = self.state.start_time
        self.state.maximum_slot = self.MAX_SLOT
        self.state.entities = self._collect_entity_snapshots()
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
                
                for e in self.entities:
                    e.tick(skyfield_time)
                    
                for l in self.links:
                    l.refresh()
                
                self.state.timestamp += self.SLOT
                self.state.slot_count += 1
                self.state.now = to_iso_string(now)
                self.state.entities = self._collect_entity_snapshots()
                self.state.links = self._collect_link_snapshots()

                # 3. 数据导出/渲染
                if self.on_render_hook:
                    # 执行回调，将 state 发送到 WebSocket
                    await self.on_render_hook(self.state.model_dump())

            # 4. 频率控制
            elapsed = time.perf_counter() - start_time
            sleep_time = max(0, self.dt - elapsed)
            await asyncio.sleep(sleep_time)

        print("[Engine] Loop terminated.")