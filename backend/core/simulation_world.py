from typing import List

import numpy as np

from core.simulation_clock import CLOCK
from entity.gs import GroundStation
from entity.sat import Satellite
from util.time_utils import skyfield_to_datetime
from status.mission_status import MissionPhase
from entity.mission import Mission
from topology.node import Node
from topology.link import Link
from entity.eth import Earth
from entity.sun import Sun
from util.const import DEFAULT_ALTITUDE, DEFAULT_CONSTELLATION_SIZE, DEFAULT_INCLINATION, DEFAULT_PHASE_FACTOR, DEFAULT_PLANE_COUNT
from util.gs_generator import generate_stations
from util.sat_generator import generate_constellation
from controller.project_controller import GroundStationBase, ProjectBase
from entity.entity import Entity
from skyfield.timelib import Time

class SimulationWorld(Entity):
    def __init__(self):
        super().__init__(type="world")
        
        self.SEED: int = 0
        
        # Environment Entities
        self.entities: List[Entity] = []
        
        # Entities Classification
        self.satellites: List[Satellite] = []
        self.ground_stations: List[GroundStation] = []
        
        # Networks
        self.nodes: List[Node] = []
        self.links: List[Link] = []
        
        # Missions
        self.missions: List[Mission] = []
        
    def setup(self, pjc_base: ProjectBase, gs_base: List[GroundStationBase]):
        self.clear()  # 清空现有数据
        
        self.SEED = pjc_base.seed
        
        # 根据项目数据创建实体
        ALT = pjc_base.altitude if pjc_base.altitude and pjc_base.altitude > 0 else DEFAULT_ALTITUDE
        INC = pjc_base.inclination if pjc_base.inclination and 0 <= pjc_base.inclination <= 180 else DEFAULT_INCLINATION
        CON_SIZE = pjc_base.sizeOfConstellation if pjc_base.sizeOfConstellation else DEFAULT_CONSTELLATION_SIZE
        P_NUM = pjc_base.maximumNumberOfPlane if pjc_base.maximumNumberOfPlane else DEFAULT_PLANE_COUNT
        PF = pjc_base.phaseFactor if pjc_base.phaseFactor else DEFAULT_PHASE_FACTOR
        
        sun = Sun()
        self.entities.append(sun)  # 添加太阳实体
        
        earth = Earth()
        self.entities.append(earth) # 添加地球实体
        
        satellites = generate_constellation(alt=ALT, inc=INC, P=P_NUM, T=CON_SIZE, F=PF)
        self.entities.extend(satellites)
        self.satellites.extend(satellites)
        self.nodes.extend(satellites)
        
        stations = generate_stations(gs_models=gs_base)
        self.entities.extend(stations)
        self.ground_stations.extend(stations)
        self.nodes.extend(stations)
        
        # 调用每个组件的 setup 方法，传入整个项目数据
        for e in self.entities:
            e.setup(pjc_base)
        
        # 根据实体列表生成链路（全连接，后续可优化为基于距离或其他规则）
        for u in self.nodes:
            for v in self.nodes:
                if u != v:
                    l = Link(src=u, dst=v)
                    l.setup(pjc_base)
                    self.links.append(l)
                    
                    
    def tick(self):
        self.missions.extend(self.generate_missions())  # 生成新的任务
        # 更新每个实体的状态
        for e in self.entities:
            e.tick()
        # 每个时刻重新计算链路状态
        for n in self.nodes:
            n.connections.clear()
        # 计算链路状态
        for l in self.links:
            l.refresh()
            if l.status:
                l.src.connections.append(l)
                
    """为了专注于Task Offloading，创立此函数生成任务从而简化仿真流程，跳过上传和观测阶段""" 
    # =============================================================================
    def generate_missions(self) -> list[Mission]:
        # 根据泊松分布和SEED生成新的Mission
        lam = 0.2 * CLOCK.SLOT
        rng = np.random.default_rng(self.SEED)
        num_missions = rng.poisson(lam)
        random_missions = []
        for i in range(num_missions):
            random_pos = rng.choice(self.satellites)  # 从卫星列表中随机选择一个位置
            mission = Mission(
                position=random_pos,
                start_time=CLOCK.current_time,
                start_slot=CLOCK.current_slot,
            )
            mission.create(
                w_px=random_pos.IMAGERY_WIDTH, 
                h_px=random_pos.IMAGERY_HEIGHT, 
                bpc=random_pos.BITS_PER_CHANNEL, 
                cpp=random_pos.CHANNELS_PER_PIXEL)
            mission.phase = MissionPhase.COMPUTING
            random_missions.append(mission)
        return random_missions
    # =============================================================================
                
                
    def clear(self):
        self.entities.clear()
        self.satellites.clear()
        self.ground_stations.clear()
        self.nodes.clear()
        self.links.clear()


WORLD = SimulationWorld()