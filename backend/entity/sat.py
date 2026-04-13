from curses.ascii import alt
from typing import Any, Dict

import numpy as np
from pydantic import BaseModel
from skyfield.api import wgs84, EarthSatellite
from skyfield.timelib import Time
from skyfield.positionlib import Geocentric
from status.mission_status import MissionPhase
from util.time_utils import skyfield_to_datetime
from entity.mission import Mission
from entity.node import Node
from controller.project_controller import ProjectBase
from entity.entity import Entity, EntityType
from util.const import EARTH, EPHEMERIS, GEOD, SUN

class SatelliteSnapshot(BaseModel):
    addr: str
    type: str
    # spatial
    id: str
    plane: int
    order: int
    lat: float
    lon: float
    alt: float
    x: float
    y: float
    z: float
    
    # Velocity Vector
    velocityVectorX: float
    velocityVectorY: float
    velocityVectorZ: float
    
    # Solar Vector
    solarVectorX: float
    solarVectorY: float
    solarVectorZ: float

    # imagery
    corLat1: float
    corLon1: float
    corLat2: float
    corLon2: float
    corLat3: float
    corLon3: float
    corLat4: float
    corLon4: float
    
    corX1: float
    corY1: float
    corZ1: float
    corX2: float
    corY2: float
    corZ2: float
    corX3: float
    corY3: float
    corZ3: float
    corX4: float
    corY4: float
    corZ4: float

    # energy
    batteryLevel: float
    processorClockFrequency: float

    # indicators
    onROI: bool
    onSGL: bool
    onCOM: bool
    onISL: bool
    onSUN: bool
    
    connections: list[str] = []

class Satellite(EarthSatellite, Node):
    def __init__(self,l1: str, l2: str, id: int = 0, plane: int = 0, order: int = 0):
        super().__init__(line1=l1, line2=l2, name=str(id))
        Node.__init__(self, EntityType.SAT)
        
        self.id = id
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
        self.battery_level: float = 100.0  # 当前电池电量
        self.processor_clock_frequency: float = 0.0  # 当前处理器时钟频率
        self.tasks_in_processing: int = 0  # 当前正在处理的任务数量
        self.tasks_in_transmitting: int = 0  # 当前正在传输的任务
        self.power_of_computing: float = 0.0  # 计算动态功率
        
        self.power_of_ISL_transmission: float = 30  # 传输动态功率
        self.power_of_DL_transmission: float = 60  # 传输动态功率
        
        self.transmit_signal_ISL_power: float = 0.0  # 发射信号功率
        self.transmit_signal_DL_power: float = 0.0  # 发射信号功率
        
        # 状态
        self.onROI: bool = True
        self.onSGL: bool = True
        self.onCOM: bool = True
        self.onISL: bool = False
        self.onSUN: bool = False
        
    def setup(self, project: ProjectBase):
        # 从项目数据中提取卫星属性
        self.IMAGERY_WIDTH = int(project.imageryWidthPx or 0)
        self.IMAGERY_HEIGHT = int(project.imageryHeightPx or 0)
        self.LENGTH_OF_CAMERA_FOCAL = float(project.lengthOfCameraFocalMm or 0.0)
        self.LENGTH_OF_CAMERA_SENSOR_UNIT = float(project.lengthOfCameraSensorUnitUm or 0.0)
        self.CHANNELS_PER_PIXEL = int(project.channelsPerPixel or 0)
        self.BITS_PER_CHANNEL = int(project.bitsPerChannelBit or 0)

        # 计算属性
        self.MAXIMUM_NUMBER_OF_PROCESSOR_CORE = int(project.maximumNumberOfProcessorCore or 0)
        self.FACTOR_OF_COMPUTATION_ENERGY = float(project.factorOfComputationEnergy or 0.0)
        self.MAXIMUM_CONCURRENT_COMPUTATION = int(project.maximumConcurrentComputation or 0)
        self.processor_clock_frequency = float(project.maximumClockFrequencyGhz or 0.0)
        
        # 通信属性
        # ISL
        self.CARRIER_FREQUENCY_OF_ISL = float(project.carrierFrequencyOfIslGhz or 0.0)
        self.BANDWIDTH_OF_ISL = float(project.bandwidthOfIslMhz or 0.0)
        self.ANTENNA_GAIN_OF_ISL_TRANSMIT = float(project.antennaGainOfIslTransmitDbi or 0.0)
        self.ANTENNA_GAIN_OF_ISL_RECEIVE = float(project.antennaGainOfIslReceiveDbi or 0.0)
        
        # Uplink
        self.CARRIER_FREQUENCY_OF_UL = float(project.carrierFrequencyOfUpGhz or 0.0)
        self.BANDWIDTH_OF_UL = float(project.bandwidthOfUlMhz or 0.0)
        self.ANTENNA_GAIN_OF_UL_RECEIVE = float(project.antennaGainOfUlReceiveDbi or 0.0)
        
        # Downlink
        self.CARRIER_FREQUENCY_OF_DL = float(project.carrierFrequencyOfDlGhz or 0.0)
        self.BANDWIDTH_OF_DL = float(project.bandwidthOfDlMhz or 0.0)
        self.ANTENNA_GAIN_OF_DL_TRANSMIT = float(project.antennaGainOfDlTransmitDbi or 0.0)
        
        self.FACTOR_OF_TRANSMISSION_ENERGY = float(project.factorOfTransmissionEnergy or 0.0)
        self.EFFICIENCY_OF_TARGET_SPECTRUM = float(project.efficiencyOfTargetSpectrum or 0.0)
        self.MAXIMUM_CONCURRENT_TRANSMISSION = int(project.maximumConcurrentTransmission or 0)
        
        # 能量属性
        self.BATTERY_CAPACITY = float(project.batteryCapacityWh or 0.0)
        self.AREA_OF_SOLAR_PANEL = float(project.areaOfSolarPanelM2 or 0.0)
        self.EFFICIENCY_OF_SOLAR_PANEL = float(project.efficiencyOfSolarPanel or 0.0)
        self.EFFICIENCY_OF_POWER_AMPLIFIER = float(project.efficiencyOfPowerAmplifier or 1)
        self.STATIC_POWER_OF_PROCESSING = float(project.staticPowerOfProcessingW or 0.0)
        self.STATIC_POWER_OF_ISL_TRANSMITTING = float(project.staticPowerOfIslTransmittingW or 0.0)
        self.STATIC_POWER_OF_DL_TRANSMITTING = float(project.staticPowerOfDownlinkTransmittingW or 0.0)
        self.STATIC_POWER_OF_OTHERS = float(project.staticPowerOfOthersW or 0.0)
        self.calc_transmit_signal_power()

    def tick(self, t: Time):
        # 1. 更新状态
        self.move(t)
        # 2. 进行观测
        state = self.observe()
        # 3. 制定策略
        action = self.decide(state)
        # 4. 执行决策
        self.act(action)
       
    """为了专注于Task Offloading，创立此函数生成任务从而简化仿真流程，跳过上传和观测阶段""" 
    # =============================================================================
    def generate_missions(self, t: Time) -> list[Mission]:
        _now = skyfield_to_datetime(t).isoformat()
        # 随机数生成器，使用卫星地址的哈希值作为种子，确保同一卫星在不同轮次生成的任务分布相似
        rng = np.random.default_rng(hash(self.address) % (2**32))
        num_missions = rng.poisson(3)  # 平均每轮生成3个任务
        random_missions = []
        for i in range(num_missions):
            mission = Mission(
                position=self,
                start_time=_now,
            )
            mission.setup(
                w_px=self.IMAGERY_WIDTH, 
                h_px=self.IMAGERY_HEIGHT, 
                bpc=self.BITS_PER_CHANNEL, 
                cpp=self.CHANNELS_PER_PIXEL)
            mission.status = MissionPhase.COMPUTING
            random_missions.append(mission)
        return random_missions
    # =============================================================================
    
    def move(self, t: Time):
        # 更新卫星状态
        geocentric = self.at(t)
        self.onSUN = geocentric.is_sunlit(EPHEMERIS)
        self.calc_position(geocentric)
        self.calc_velocity_vector(geocentric)
        self.calc_solar_vector(t, geocentric)
        self.calc_subpoint(geocentric)
        self.calc_footprint(t)
        # 生成任务
        self.missions.extend(self.generate_missions(t))
        
    def observe(self) -> Dict[str, Any]:
        pass 
   
    def decide(self, state: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    def act(self, action: Dict[str, Any]):
        pass

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
        computing_power = self.MAXIMUM_NUMBER_OF_PROCESSOR_CORE * self.FACTOR_OF_COMPUTATION_ENERGY * self.processor_clock_frequency ** 3
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

        self.cor_lat_1, self.cor_lon_1 = float(lats_out[0]), float(lons_out[0])
        self.cor_lat_2, self.cor_lon_2 = float(lats_out[1]), float(lons_out[1])
        self.cor_lat_3, self.cor_lon_3 = float(lats_out[2]), float(lons_out[2])
        self.cor_lat_4, self.cor_lon_4 = float(lats_out[3]), float(lons_out[3])

        self.cor_x_1, self.cor_y_1, self.cor_z_1 = wgs84.latlon(self.cor_lat_1, self.cor_lon_1).at(t).position.m
        self.cor_x_2, self.cor_y_2, self.cor_z_2 = wgs84.latlon(self.cor_lat_2, self.cor_lon_2).at(t).position.m
        self.cor_x_3, self.cor_y_3, self.cor_z_3 = wgs84.latlon(self.cor_lat_3, self.cor_lon_3).at(t).position.m
        self.cor_x_4, self.cor_y_4, self.cor_z_4 = wgs84.latlon(self.cor_lat_4, self.cor_lon_4).at(t).position.m
    
    def snapshot(self):
        return SatelliteSnapshot(
            addr=self.address,
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
            velocityVectorX=self.velocity_vector_x,
            velocityVectorY=self.velocity_vector_y,
            velocityVectorZ=self.velocity_vector_z,
            solarVectorX=self.solar_vector_x,
            solarVectorY=self.solar_vector_y,
            solarVectorZ=self.solar_vector_z,
            corLat1=self.cor_lat_1,
            corLon1=self.cor_lon_1,
            corLat2=self.cor_lat_2,
            corLon2=self.cor_lon_2,
            corLat3=self.cor_lat_3,
            corLon3=self.cor_lon_3,
            corLat4=self.cor_lat_4,
            corLon4=self.cor_lon_4,
            corX1=self.cor_x_1,
            corY1=self.cor_y_1,
            corZ1=self.cor_z_1,
            corX2=self.cor_x_2,
            corY2=self.cor_y_2,
            corZ2=self.cor_z_2,
            corX3=self.cor_x_3,
            corY3=self.cor_y_3,
            corZ3=self.cor_z_3,
            corX4=self.cor_x_4,
            corY4=self.cor_y_4,
            corZ4=self.cor_z_4,
            batteryLevel=self.battery_level,
            processorClockFrequency=self.processor_clock_frequency,
            onROI=self.onROI,
            onSGL=self.onSGL,
            onCOM=self.onCOM,
            onISL=self.onISL,
            onSUN=self.onSUN,
            connections=self.list_connection_addresses(),
        )
        
    def serialize(self) -> dict[str, Any]:
        return self.snapshot().model_dump()