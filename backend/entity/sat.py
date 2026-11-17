import math
from typing import Any, Dict

import numpy as np
from pydantic import BaseModel
from skyfield.api import wgs84, EarthSatellite
from skyfield.timelib import Time
from skyfield.positionlib import Geocentric
from algorithm.algo import Algorithm
from algorithm.algo_manager import ALGO_MANAGER
from core.simulation_clock import CLOCK
from topology.node import Node
from simulator.schemas.engine_config import EngineConfig
from entity.entity import Entity, EntityType
from util.const import EARTH, EPHEMERIS, GEOD, SUN

from entity.satellite_snapshot import SatelliteSnapshot

class Satellite(EarthSatellite, Node):
    def __init__(self,l1: str, l2: str, id: int = 0, plane: int = 0, order: int = 0):
        super().__init__(line1=l1, line2=l2, name=str(id))
        Node.__init__(self, EntityType.SAT)
        
        self.id = str(id)
        self.plane = plane
        self.order = order
        self.azimuth = 0.0
        
        # 地面投影点坐标 (lat, lon, alt)
        self.lat = 0.0
        self.lon = 0.0
        self.alt = 0.0
        self.inc = 0.0
        
        # ECEF 坐标
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        
        # Velocity Vector
        self.velocity_vector_x: float = 0.0
        self.velocity_vector_y: float = 0.0
        self.velocity_vector_z: float = 0.0
        
        # Solar Vector
        self.solar_vector_x: float = 0.0
        self.solar_vector_y: float = 0.0
        self.solar_vector_z: float = 0.0
        
        # 4 footprint corners (lat, lon)
        self.cor_lat1 = 0.0
        self.cor_lon1 = 0.0
        self.cor_lat2 = 0.0
        self.cor_lon2 = 0.0
        self.cor_lat3 = 0.0
        self.cor_lon3 = 0.0
        self.cor_lat4 = 0.0
        self.cor_lon4 = 0.0
        
        # 4 footprint corners (x, y, z)
        self.cor_x1 = 0.0
        self.cor_y1 = 0.0
        self.cor_z1 = 0.0
        self.cor_x2 = 0.0
        self.cor_y2 = 0.0
        self.cor_z2 = 0.0
        self.cor_x3 = 0.0
        self.cor_y3 = 0.0
        self.cor_z3 = 0.0
        self.cor_x4 = 0.0
        self.cor_y4 = 0.0
        self.cor_z4 = 0.0
        
        self.SLOT: int = 0
        
        # 观测参数
        self.IMAGERY_WIDTH: int = 0
        self.IMAGERY_HEIGHT: int = 0
        self.LENGTH_OF_CAMERA_FOCAL: float = 0.0
        self.LENGTH_OF_CAMERA_SENSOR_UNIT: float = 0.0
        self.CHANNELS_PER_PIXEL: int = 0
        self.BITS_PER_CHANNEL: int = 0
        
        # 计算属性
        self.FACTOR_OF_COMPUTATION_ENERGY: float = 0.0
        self.MAXIMUM_CONCURRENT_COMPUTATION: int = 0
        self.MAXIMUM_NUMBER_OF_PROCESSOR_CORE: int = 0
        self.MAXIMUM_CLOCK_FREQUENCY: float = 0.0
        
        
        # 通信属性
        self.CARRIER_FREQUENCY_OF_ISL: float = 0.0
        self.CARRIER_FREQUENCY_OF_UL: float = 0.0
        self.CARRIER_FREQUENCY_OF_DL: float = 0.0
        
        self.BANDWIDTH_OF_ISL: float = 0.0
        self.BANDWIDTH_OF_UL: float = 0.0
        self.BANDWIDTH_OF_DL: float = 0.0
        
        self.FACTOR_OF_TRANSMISSION_ENERGY: float = 0.0
        
        self.EFFICIENCY_OF_TARGET_SPECTRUM: float = 0.0
        
        self.ANTENNA_GAIN_OF_ISL_TRANSMIT: float = 0.0
        # self.ANTENNA_GAIN_OF_UP_TRANSMIT: float = 0.0
        self.ANTENNA_GAIN_OF_DL_TRANSMIT: float = 0.0
        self.ANTENNA_GAIN_OF_ISL_RECEIVE: float = 0.0
        self.ANTENNA_GAIN_OF_UL_RECEIVE: float = 0.0
        # self.ANTENNA_GAIN_OF_DL_RECEIVE: float = 0.0
        self.MAXIMUM_CONCURRENT_TRANSMISSION: int = 0
        
        # 能量属性
        self.BATTERY_CAPACITY: float = 0.0  # 电池容量
        self.AREA_OF_SOLAR_PANEL: float = 0.0  # 太阳能板面积
        self.EFFICIENCY_OF_SOLAR_PANEL: float = 0.0  # 太阳能板效率
        self.EFFICIENCY_OF_POWER_AMPLIFIER: float = 0.0
        
        self.STATIC_POWER_OF_PROCESSING: float = 0.0  # 计算静态功率
        self.STATIC_POWER_OF_ISL_TRANSMITTING: float = 0.0  # 传输静态功率
        self.STATIC_POWER_OF_DL_TRANSMITTING: float = 0.0  # 传输静态功率
        # self.STATIC_POWER_OF_UP_TRANSMITTING: float = 0.0  # 传输静态功率
        self.STATIC_POWER_OF_OTHERS: float = 0.0  # 其他静态功率
        
        # 动态变量
        self.battery_percent: float = 100.0  # 当前电池电量
        self.processor_clock_frequency_ghz: float = 0.0  # 当前处理器时钟频率
        self.tasks_in_processing: int = 0  # 当前正在处理的任务数量
        self.tasks_in_transmitting: int = 0  # 当前正在传输的任务
        self.power_of_computing: float = 0.0  # 计算动态功率
        
        self.power_of_ISL_transmission: float = 30  # 传输动态功率
        self.power_of_DL_transmission: float = 60  # 传输动态功率
        
        self.transmit_signal_ISL_power: float = 0.0  # 发射信号功率
        self.transmit_signal_DL_power: float = 0.0  # 发射信号功率
        
        self.power_of_solar_panel: float = 0.0  # 太阳能板功率
        
        # 状态
        self.is_observing: bool = True
        self.is_communicating_sgl: bool = True
        self.is_processing: bool = True
        self.is_communicating_isl: bool = False
        self.is_charging: bool = False
        
        # 任务列表

        # 可插拔算法（感知 -> 决策 -> 执行）
        self.algorithm_name: str = "phoenix"
        self.algorithm: Algorithm = ALGO_MANAGER.create(self.algorithm_name)
        
    def setup(self, project: EngineConfig):
        
        # 从项目数据中提取卫星属性
        self.IMAGERY_WIDTH = int(project.width_px or 0)
        self.IMAGERY_HEIGHT = int(project.length_px or 0)
        self.LENGTH_OF_CAMERA_FOCAL = float(project.focal_length_mm or 0.0)
        self.LENGTH_OF_CAMERA_SENSOR_UNIT = float(project.pixel_size_um or 0.0)
        self.CHANNELS_PER_PIXEL = int(project.channels_per_pixel or 0)
        self.BITS_PER_CHANNEL = int(project.bits_per_channel or 0)

        # 计算属性
        self.MAXIMUM_NUMBER_OF_PROCESSOR_CORE = int(project.processor_core_count or 0)
        self.FACTOR_OF_COMPUTATION_ENERGY = float(project.computation_energy_factor or 0.0)
        self.MAXIMUM_CONCURRENT_COMPUTATION = int(project.max_concurrent_computations or 0)
        self.processor_clock_frequency_ghz = float(project.max_clock_frequency_ghz or 0.0)
        
        # 通信属性
        # ISL
        self.CARRIER_FREQUENCY_OF_ISL = float(project.isl_frequency_ghz or 0.0)
        self.BANDWIDTH_OF_ISL = float(project.isl_bandwidth_mhz or 0.0)
        self.ANTENNA_GAIN_OF_ISL_TRANSMIT = float(project.isl_gain_tx_dbi or 0.0)
        self.ANTENNA_GAIN_OF_ISL_RECEIVE = float(project.isl_gain_rx_dbi or 0.0)
        
        # Uplink
        self.CARRIER_FREQUENCY_OF_UL = float(project.uplink_frequency_ghz or 0.0)
        self.BANDWIDTH_OF_UL = float(project.uplink_bandwidth_mhz or 0.0)
        self.ANTENNA_GAIN_OF_UL_RECEIVE = float(project.uplink_gain_rx_dbi or 0.0)
        
        # Downlink
        self.CARRIER_FREQUENCY_OF_DL = float(project.downlink_frequency_ghz or 0.0)
        self.BANDWIDTH_OF_DL = float(project.downlink_bandwidth_mhz or 0.0)
        self.ANTENNA_GAIN_OF_DL_TRANSMIT = float(project.downlink_gain_tx_dbi or 0.0)
        
        self.FACTOR_OF_TRANSMISSION_ENERGY = float(project.transmission_energy_factor or 0.0)
        self.EFFICIENCY_OF_TARGET_SPECTRUM = float(project.spectral_efficiency or 0.0)
        self.MAXIMUM_CONCURRENT_TRANSMISSION = int(project.max_concurrent_transmissions or 0)
        
        # 能量属性
        self.BATTERY_CAPACITY = float(project.battery_capacity_wh or 0.0)
        self.AREA_OF_SOLAR_PANEL = float(project.solar_panel_area_m2 or 0.0)
        self.EFFICIENCY_OF_SOLAR_PANEL = float(project.solar_panel_efficiency or 0.0)
        self.EFFICIENCY_OF_POWER_AMPLIFIER = float(project.amplifier_efficiency or 1)
        self.STATIC_POWER_OF_PROCESSING = float(project.static_processing_power_w or 0.0)
        self.STATIC_POWER_OF_ISL_TRANSMITTING = float(project.static_isl_power_w or 0.0)
        self.STATIC_POWER_OF_DL_TRANSMITTING = float(project.static_downlink_power_w or 0.0)
        self.STATIC_POWER_OF_OTHERS = float(project.static_other_power_w or 0.0)
        self.calc_transmit_signal_power()
        
        self.power_of_solar_panel = self.AREA_OF_SOLAR_PANEL * self.EFFICIENCY_OF_SOLAR_PANEL * 1361  # 太阳常数约为 1361 W/m^2

    def tick(self):
        # 1. 更新状态
        self.move()
        # 2. 进行观测
        state = self.observe()
        # 3. 制定策略
        action = self.decide(state)
        # 4. 执行决策
        self.act(action)
       
    
    def move(self):
        # 更新卫星状态
        geocentric = self.at(CLOCK.current_time)
        self.is_charging = bool(geocentric.is_sunlit(EPHEMERIS))
        self.calc_position(geocentric)
        self.calc_velocity_vector(geocentric)
        self.calc_solar_vector(CLOCK.current_time, geocentric)
        self.calc_subpoint(geocentric)
        self.calc_footprint(CLOCK.current_time)
        # 生成任务
        # self.missions.extend(self.generate_missions(CLOCK.current_time, CLOCK.current_slot))
        
    def is_sunlit(self, t: Time) -> bool:
        geocentric = self.at(t)
        return geocentric.is_sunlit(EPHEMERIS)
    
    def sunlit_slots_in_period(self, start: Time, slots_num: int) -> list[int]:
        """计算在给定时间段内卫星处于日照状态的时间槽列表"""
        sunlit_slots = 0
        for i in range(slots_num):
            t = start + i * self.SLOT
            if self.is_sunlit(t):
                sunlit_slots += 1
        return sunlit_slots

    def set_algorithm(self, name: str):
        self.algorithm_name = name
        self.algorithm = ALGO_MANAGER.create(name)
        
    def observe(self) -> Dict[str, Any]:
        return self.algorithm.observe(self)
   
    def decide(self, state: Dict[str, Any]) -> Dict[str, Any]:
        return self.algorithm.decide(self, state)
    
    def act(self, action: Dict[str, Any]):
        self.algorithm.act(self, action)
        
    def get_orbital_cycle(self) -> tuple[float, int]:
        """计算卫星的轨道周期，单位为秒"""
        # SGP4 mean motion: radians per minute.
        mean_motion_rad_per_min = float(self.model.no_kozai or 0.0)

        if mean_motion_rad_per_min <= 0.0:
            return 0.0

        orbital_cycle_min = (2.0 * np.pi) / mean_motion_rad_per_min
        seconds = float(orbital_cycle_min * 60.0)
        slots = math.ceil(seconds / CLOCK.SLOT) if CLOCK.SLOT > 0 else 0
        return seconds, slots

    def calc_transmit_signal_power(self):
        # 简化模型：假设发射功率与带宽成正比
        self.transmit_signal_ISL_power = max(
            self.EFFICIENCY_OF_POWER_AMPLIFIER
            * (self.power_of_ISL_transmission - self.STATIC_POWER_OF_ISL_TRANSMITTING),
            0.0,
        )
        self.transmit_signal_DL_power = max(
            self.EFFICIENCY_OF_POWER_AMPLIFIER
            * (self.power_of_DL_transmission - self.STATIC_POWER_OF_DL_TRANSMITTING),
            0.0,
        )

    def calc_velocity_vector(self, geocentric: Geocentric):
        # geocentric.velocity.m_per_s is a 3D instantaneous velocity vector [vx, vy, vz].
        velocity = geocentric.velocity.m_per_s
        norm = np.linalg.norm(velocity)
        if norm <= 0:
            self.velocity_vector_x = 0.0
            self.velocity_vector_y = 0.0
            self.velocity_vector_z = 0.0
            return

        unit_velocity_vector = velocity / norm
        self.velocity_vector_x = float(unit_velocity_vector[0])
        self.velocity_vector_y = float(unit_velocity_vector[1])
        self.velocity_vector_z = float(unit_velocity_vector[2])

    def calc_solar_vector(self, t: Time, geocentric: Geocentric):
        ast_sun = EARTH.at(t).observe(SUN)
        sun_xyz = ast_sun.apparent().position.m
        sat_xyz = geocentric.position.m
        sun_vec = sun_xyz - sat_xyz
        norm = np.linalg.norm(sun_vec)
        unit_solar_vector = sun_vec / norm
        self.solar_vector_x = unit_solar_vector[0]
        self.solar_vector_y = unit_solar_vector[1]
        self.solar_vector_z = unit_solar_vector[2]
        
    def calc_dpc(self) -> float:
        """计算计算动态功率 (DPC)，单位 W"""
        computing_power = self.MAXIMUM_NUMBER_OF_PROCESSOR_CORE * self.FACTOR_OF_COMPUTATION_ENERGY * self.processor_clock_frequency_ghz ** 3
        return computing_power
    
    def calc_dpt(self) -> float:
        """计算传输动态功率 (DPT)，单位 W"""
        circuit_power = 2 # 假设电路功耗为 2 W
        eta = 0.25
        num_of_links = 4
        transmitting_power = num_of_links * self.STATIC_POWER_OF_ISL_TRANSMITTING / eta + circuit_power
        return transmitting_power
        
    def calc_position(self, geocentric: Geocentric):
        sat_xyz = geocentric.position.m
        self.x, self.y, self.z = sat_xyz
        
    def calc_subpoint(self, geocentric: Geocentric):
        subpoint = geocentric.subpoint()
        self.lat = subpoint.latitude.degrees
        self.lon = subpoint.longitude.degrees
        self.alt = subpoint.elevation.m
        
    def calc_footprint(self, t: Time):
        # 计算卫星的 footprint 角点坐标
        if self.alt <= 0:
            return

        if self.LENGTH_OF_CAMERA_FOCAL <= 0 or self.LENGTH_OF_CAMERA_SENSOR_UNIT <= 0:
            return

        if self.IMAGERY_WIDTH <= 0 or self.IMAGERY_HEIGHT <= 0:
            return

        focal_m = self.LENGTH_OF_CAMERA_FOCAL * 1e-3
        sensor_unit_m = self.LENGTH_OF_CAMERA_SENSOR_UNIT * 1e-6

        swath_w = self.alt * (self.IMAGERY_WIDTH * sensor_unit_m) / focal_m
        swath_l = self.alt * (self.IMAGERY_HEIGHT * sensor_unit_m) / focal_m

        half_w = swath_w / 2
        half_l = swath_l / 2

        lon0 = self.lon
        lat0 = self.lat

        # offsets: (dy, dx) 顺序为 NE, NW, SW, SE
        offsets = [
            (half_l, half_w),    # NE
            (half_l, -half_w),   # NW
            (-half_l, -half_w),  # SW
            (-half_l, half_w),   # SE
        ]

        azs = []
        dists = []
        for dy, dx in offsets:
            az = (np.degrees(np.arctan2(dx, dy))) % 360
            dist = float(np.sqrt(dx ** 2 + dy ** 2))
            azs.append(az)
            dists.append(dist)

        lons_out, lats_out, _ = GEOD.fwd(
            np.full(4, lon0),
            np.full(4, lat0),
            np.array(azs),
            np.array(dists),
        )
        lons_out = ((lons_out + 180) % 360) - 180

        self.cor_lat1, self.cor_lon1 = float(lats_out[0]), float(lons_out[0])
        self.cor_lat2, self.cor_lon2 = float(lats_out[1]), float(lons_out[1])
        self.cor_lat3, self.cor_lon3 = float(lats_out[2]), float(lons_out[2])
        self.cor_lat4, self.cor_lon4 = float(lats_out[3]), float(lons_out[3])

        self.cor_x1, self.cor_y1, self.cor_z1 = wgs84.latlon(self.cor_lat1, self.cor_lon1).at(t).position.m
        self.cor_x2, self.cor_y2, self.cor_z2 = wgs84.latlon(self.cor_lat2, self.cor_lon2).at(t).position.m
        self.cor_x3, self.cor_y3, self.cor_z3 = wgs84.latlon(self.cor_lat3, self.cor_lon3).at(t).position.m
        self.cor_x4, self.cor_y4, self.cor_z4 = wgs84.latlon(self.cor_lat4, self.cor_lon4).at(t).position.m
    
    def snapshot(self):
        return SatelliteSnapshot(
            addr=self.addr,
            type=self.type,
            id=self.id,
            plane=self.plane,
            order=self.order,
            lat=self.lat,
            lon=self.lon,
            alt=self.alt,
            x=self.x,
            y=self.y,
            z=self.z,
            velocity_vector_x=self.velocity_vector_x,
            velocity_vector_y=self.velocity_vector_y,
            velocity_vector_z=self.velocity_vector_z,
            solar_vector_x=self.solar_vector_x,
            solar_vector_y=self.solar_vector_y,
            solar_vector_z=self.solar_vector_z,
            cor_lat1=self.cor_lat1,
            cor_lon1=self.cor_lon1,
            cor_lat2=self.cor_lat2,
            cor_lon2=self.cor_lon2,
            cor_lat3=self.cor_lat3,
            cor_lon3=self.cor_lon3,
            cor_lat4=self.cor_lat4,
            cor_lon4=self.cor_lon4,
            cor_x1=self.cor_x1,
            cor_y1=self.cor_y1,
            cor_z1=self.cor_z1,
            cor_x2=self.cor_x2,
            cor_y2=self.cor_y2,
            cor_z2=self.cor_z2,
            cor_x3=self.cor_x3,
            cor_y3=self.cor_y3,
            cor_z3=self.cor_z3,
            cor_x4=self.cor_x4,
            cor_y4=self.cor_y4,
            cor_z4=self.cor_z4,
            battery_percent=self.battery_percent,
            processor_clock_frequency_ghz=self.processor_clock_frequency_ghz,
            is_observing=self.is_observing,
            is_communicating_sgl=self.is_communicating_sgl,
            is_processing=self.is_processing,
            is_communicating_isl=self.is_communicating_isl,
            is_charging=self.is_charging,
            connections=self.list_connection_addresses(),
        )
        
    def serialize(self) -> dict[str, Any]:
        return self.snapshot().model_dump()