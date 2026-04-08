from typing import Dict

import numpy as np
from skyfield.api import wgs84, load, EarthSatellite
from skyfield.timelib import Time
from skyfield.positionlib import Geocentric
from backend.model.node import NodeStatus
from backend.util.const import GEOD

class Satellite(EarthSatellite):
    def __init__(self,l1: str, l2: str, id: int = 0):
        super().__init__(line1=l1, line2=l2, name=id)
        
        self.id = id
        self.status = NodeStatus.ACTIVE
        
        self.plane = 0
        self.order = 0
        self.inc = 0.0
        self.azimuth = 0.0
        
        # 地面投影点坐标 (lat, lon, alt)
        self.lat = 0.0
        self.lon = 0.0
        self.alt = 0.0
        
        # ECEF 坐标
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        
        # 4 footprint corners (lat, lon)
        self.cor_lat_1 = 0.0
        self.cor_lon_1 = 0.0
        self.cor_lat_2 = 0.0
        self.cor_lon_2 = 0.0
        self.cor_lat_3 = 0.0
        self.cor_lon_3 = 0.0
        self.cor_lat_4 = 0.0
        self.cor_lon_4 = 0.0
        
        # 4 footprint corners (x, y, z)
        self.cor_x_1 = 0.0
        self.cor_y_1 = 0.0
        self.cor_z_1 = 0.0
        self.cor_x_2 = 0.0
        self.cor_y_2 = 0.0
        self.cor_z_2 = 0.0
        self.cor_x_3 = 0.0
        self.cor_y_3 = 0.0
        self.cor_z_3 = 0.0
        self.cor_x_4 = 0.0
        self.cor_y_4 = 0.0
        self.cor_z_4 = 0.0
        
        # 观测参数
        self.IMAGERY_WIDTH: int = 0
        self.IMAGERY_LENGTH: int = 0
        self.CAMERA_FOCAL_LENGTH: float = 0.0
        self.CAMERA_SENSOR_UNIT_LENGTH: float = 0.0
        self.CHANNELS_PER_PIXEL: int = 0
        self.BITS_PER_CHANNEL: int = 0
        
        # 计算属性
        self.PROCESSOR_CORE_QUANTITY: int = 0
        self.PROCESSOR_ENERGY_FACTOR: float = 0.0
        self.MAXIMUM_TASK_PROCESSING_NUMBER: int = 0
        
        # 通信属性
        self.TRANSMIT_ANTENNA_GAIN: float = 0.0  # 发射天线增益
        self.RECEIVE_ANTENNA_GAIN: float = 0.0   # 接收天线增益
        self.TRANSMIT_SIGNAL_POWER: float = 0.0  # 发射信号功率
        self.MAXIMUM_TASK_TRANSMITTING_NUMBER: int = 0  # 最大任务传输数量
        
        # 能量属性
        self.BATTERY_CAPACITY: float = 0.0  # 电池容量
        self.SOLAR_PANEL_AREA: float = 0.0  # 太阳能板面积
        self.SOLAR_PANEL_EFFICIENCY: float = 0.0  # 太阳能板效率
        self.STATIC_POWER_OF_COMPUTING: float = 0.0  # 计算静态功率
        self.STATIC_POWER_OF_TRANSMITTING: float = 0.0  # 传输静态功率
        self.STATIC_POWER_OF_OTHERS: float = 0.0  # 其他静态功率
        
        # 动态变量
        self.battery_level: float = 100.0  # 当前电池电量
        self.tasks_in_processing: int = 0  # 当前正在处理的任务数量
        self.tasks_in_transmitting: int = 0  # 当前正在传输的任务
        self.dynamic_power_of_computing: float = 0.0  # 计算动态功率
        self.dynamic_power_of_transmitting: float = 0.0  # 传输动态功率
        
        #决策变量
        self.processor_clock_frequency: float = 0.0  # 当前处理器时钟频率
        self.process_target: float = 0.0  # 当前处理器时钟频率
        
        # 状态
        self.is_in_sunlight = True
        self.is_processing = False
        self.is_transmitting = False
        
    def calc_dpc(self) -> float:
        """计算计算动态功率 (DPC)，单位 W"""
        computing_power = self.PROCESSOR_CORE_QUANTITY * self.PROCESSOR_ENERGY_FACTOR * self.processor_clock_frequency ** 3
        return computing_power
    
    def calc_dpt(self) -> float:
        """计算传输动态功率 (DPT)，单位 W"""
        circuit_power = 2 # 假设电路功耗为 2 W
        eta = 0.25
        num_of_links = 4
        transmitting_power = num_of_links * self.STATIC_POWER_OF_TRANSMITTING / eta + circuit_power
        return transmitting_power

    def update(self, t: Time):
        # 更新卫星状态
        geocentric = self.at(t)
        # 1. 更新位置和姿态
        self.compute_position(geocentric)
        self.compute_subpoint(geocentric)
        self.compute_footprint(t)
        
    def compute_position(self, geocentric: Geocentric):
        self.x, self.y, self.z = geocentric.position.m
        
    def compute_subpoint(self, geocentric: Geocentric):
        subpoint = geocentric.subpoint()
        self.lat = subpoint.latitude.degrees
        self.lon = subpoint.longitude.degrees
        self.alt = subpoint.elevation.m
        
    def compute_footprint(self, t: Time):
        # 计算卫星的 footprint 角点坐标
        if self.alt <= 0:
            return

        if self.CAMERA_FOCAL_LENGTH <= 0 or self.CAMERA_SENSOR_UNIT_LENGTH <= 0:
            return

        if self.IMAGERY_WIDTH <= 0 or self.IMAGERY_LENGTH <= 0:
            return

        focal_m = self.CAMERA_FOCAL_LENGTH * 1e-3
        sensor_unit_m = self.CAMERA_SENSOR_UNIT_LENGTH * 1e-6

        swath_w = self.alt * (self.IMAGERY_WIDTH * sensor_unit_m) / focal_m
        swath_l = self.alt * (self.IMAGERY_LENGTH * sensor_unit_m) / focal_m

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

        self.cor_lat_1, self.cor_lon_1 = float(lats_out[0]), float(lons_out[0])
        self.cor_lat_2, self.cor_lon_2 = float(lats_out[1]), float(lons_out[1])
        self.cor_lat_3, self.cor_lon_3 = float(lats_out[2]), float(lons_out[2])
        self.cor_lat_4, self.cor_lon_4 = float(lats_out[3]), float(lons_out[3])

        self.cor_x_1, self.cor_y_1, self.cor_z_1 = wgs84.latlon(self.cor_lat_1, self.cor_lon_1).at(t).position.m
        self.cor_x_2, self.cor_y_2, self.cor_z_2 = wgs84.latlon(self.cor_lat_2, self.cor_lon_2).at(t).position.m
        self.cor_x_3, self.cor_y_3, self.cor_z_3 = wgs84.latlon(self.cor_lat_3, self.cor_lon_3).at(t).position.m
        self.cor_x_4, self.cor_y_4, self.cor_z_4 = wgs84.latlon(self.cor_lat_4, self.cor_lon_4).at(t).position.m

    
    def get_state(self):
        state = super().get_state()
        state.update({
            "type": "satellite",
            "battery": round(self.battery_level, 2),
            "sunlit": self.is_in_sunlight
        })
        return state