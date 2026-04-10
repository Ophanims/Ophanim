import enum
import math

import numpy as np
from pydantic import BaseModel
from controller.project_controller import ProjectBase
from entity.sat import Satellite
from entity.gs import GroundStation
from entity.entity import Entity, EntityType
from util.const import R_EARTH

class LinkType(enum.Enum):
    ISL = "ISL"  # 卫星间链路
    SGL = "SGL"  # 卫星-地面链路
    TL = "TL"    # 地面链路
    
    
class LinkSnapshot(BaseModel):
    id: str
    src: str
    dst: str
    type: str
    status: bool
    snr: float
    distance: float
    line_of_sight: float
    bandwidth: float
    capacity: float

class Link:
    """
    链路类：处理节点间的通信逻辑
    """
    def __init__(self, src: Entity, dst: Entity):
        self.id = f"({src.address},{dst.address})"
        self.src = src
        self.dst = dst
        self.type = LinkType.SGL          # ISL, SGL, TL
        self.status = False              # 是否连通
        
        self.MAX_PLANE = 0
        
        # 物理参数
        self.snr = 0.0                   # 信噪比 (dB)
        self.distance = 0.0              # m
        self.line_of_sight = 0.0         # m
        self.bandwidth = 20e6            # Hz (默认 20 MHz)
        self.capacity = 0.0              # bps
        self.loss = 0.0
        
    def setup(self, project: ProjectBase):
        self.MAX_PLANE = project.planeCount

    def refresh(self):
        self.type = self.getType()
        
        self.distance = self.calc_euclidean_distance()
        
        # 判断物理上是否连通 (视距)
        self.status = self.check_connectivity()
        
        if self.status:
            # 1. 先算基础损耗
            self.loss = self.calc_fspl() 
            # 2. 算 SNR (返回 dB)
            self.snr = self.calc_signal_to_noise_ratio() 
            # 3. 算实际数据吞吐量 capacity (bps)
            self.capacity = self.calc_capacity()
        else:
            self.loss = float('inf')
            # JSON 不支持 Infinity，使用有限的低 SNR 哨兵值。
            self.snr = -120.0
            self.capacity = 0.0
            
    def getType(self) -> LinkType:
        if self.src.type == EntityType.SAT \
            and self.dst.type == EntityType.SAT:
            # inter-satellite link
            return LinkType.ISL
        elif self.src.type == EntityType.GS \
            and self.dst.type == EntityType.GS:
            # terrestrial link
            return LinkType.TL
        else:
            # satellite-ground link
            return LinkType.SGL
        
    def check_connectivity(self) -> bool:

        if self.type == LinkType.SGL:
            # 确保 theta >= 10
            elv = self.calc_elevation_angle()
            return elv >= 10.0
        else:
            if not abs(self.src.plane - self.dst.plane) == self.MAX_PLANE - 1:
                return False
            
            # ISL 使用视距公式
            self.line_of_sight = self.calc_line_of_sight() 
            return self.distance < self.line_of_sight
    
    def calc_line_of_sight(self) -> float:
        """计算两节点间的视距"""
        
        los = 0.0
        
        if isinstance(self.src, Satellite) and \
        isinstance(self.dst, Satellite):
            
            s_alt = self.src.alt
            d_alt = self.dst.alt
            
            los = (math.sqrt(s_alt * (2 * R_EARTH + s_alt)) + 
            math.sqrt(d_alt * (2 * R_EARTH + d_alt)))

        return los
    
    def calc_euclidean_distance(self) -> float:
        """计算两节点间的欧氏距离"""
        s = [self.src.x, self.src.y, self.src.z]
        d = [self.dst.x, self.dst.y, self.dst.z]

        s_vec = np.array(s, dtype=float)
        d_vec = np.array(d, dtype=float)
        
        return float(np.linalg.norm(s_vec - d_vec))
    
    def calc_signal_to_noise_ratio(self) -> float:
        """计算信噪比 (SNR)，单位 dB"""
        
        if not isinstance(self.src, Satellite) and not isinstance(self.src, GroundStation):
            return 0.0
        
        if not isinstance(self.dst, Satellite) and not isinstance(self.dst, GroundStation):
            return 0.0
        
        # 1. 发射端参数 (EIRP)
        tx_power_dbw = 10 * math.log10(self.src.TRANSMIT_SIGNAL_POWER) # 假设输入是 W
        tx_gain_dbi = self.src.TRANSMIT_ANTENNA_GAIN # 假设已经是 dBi
        eirp = tx_power_dbw + tx_gain_dbi

        # 2. 空间损耗
        fspl_db = self.calc_fspl() # 例如 150 dB
        
        # 3. 大气衰减 (dB)
        # 你的 calc_attenuation_factor 返回的是线性系数 (0.8)，这里转成 dB 损耗
        af_linear = self.calc_attenuation_factor()
        atm_loss_db = -10 * math.log10(af_linear) if af_linear > 0 else 0 

        # 4. 接收端功率 (dBW)
        rx_gain_dbi = self.dst.RECEIVE_ANTENNA_GAIN
        received_power_dbw = eirp - fspl_db - atm_loss_db + rx_gain_dbi

        # 5. 噪声功率 (dBW)
        k_dbw = -228.6 # 玻尔兹曼常数 10*log10(1.38e-23)
        T = 290 # K
        temperature_dbk = 10 * math.log10(T)
        bandwidth_dbhz = 10 * math.log10(self.bandwidth)
        
        # Noise Figure 应该是接收机的固有属性，假设为 3 dB
        noise_figure_db = 3.0 
        
        noise_power_dbw = k_dbw + temperature_dbk + bandwidth_dbhz + noise_figure_db

        # 6. 计算 SNR (dB)
        snr_db = received_power_dbw - noise_power_dbw
        
        return snr_db
        
    def calc_capacity(self) -> float:
        """根据 SNR 和 Shannon 定律计算信道最大传输速率 (bps)"""
        if self.snr < -20: # 信号太弱，无法同步
            return 0.0
        
        snr_db = self.snr # 假设已经在 update_metrics 中算好并赋给 self.snr
        
        # 将 dB 转换回线性比值
        snr_linear = 10 ** (snr_db / 10.0)
        
        if snr_linear <= 0:
            return 0.0
        
        # self.bandwidth 是物理带宽 Hz
        capacity_bps = self.bandwidth * math.log2(1 + snr_linear)
        return capacity_bps
        
    def calc_attenuation_factor(self) -> float:
        """计算大气衰减因子，简化模型"""
        if self.type == LinkType.ISL:
            return 1.0  # 卫星间无大气衰减
        elif self.type == LinkType.SGL:
            return 0.8  # 卫星-地面链路有一定衰减
        else:
            return 0.9  # 地面链路有轻微衰减

    @staticmethod
    def _json_safe_number(value: float, fallback: float = 0.0) -> float:
        return float(value) if isinstance(value, (int, float)) and math.isfinite(value) else fallback
        
    def calc_fspl(self) -> float:
        if self.distance <= 0:
            return 0.0
            
        c = 3e8
        f = 2e9
        carrier_wavelength = c / f
        
        # 展开为对数相加：20*log10(d) + 20*log10(4*pi/lambda)
        fspl_db = 20 * math.log10(self.distance) + \
            20 * math.log10((4 * math.pi) / carrier_wavelength)
        return fspl_db
    
    def calc_elevation_angle(self) -> float:
        """计算地面站对卫星的仰角 (SGL 专用)"""
        # 确保 gs 是地面站，sat 是卫星
        gs = self.src if isinstance(self.src, GroundStation) else self.dst
        sat = self.dst if isinstance(self.dst, Satellite) else self.src

        p_gs = np.array([gs.x, gs.y, gs.z])
        p_sat = np.array([sat.x, sat.y, sat.z])

        # 站星向量
        r_gs_sat = p_sat - p_gs
        # 地面站法向量 (简化处理，指向地心反方向)
        n_gs = p_gs / np.linalg.norm(p_gs)

        # 计算仰角
        sin_el = np.dot(r_gs_sat, n_gs) / np.linalg.norm(r_gs_sat)
        return math.degrees(math.asin(max(-1.0, min(1.0, sin_el))))

    def snapshot(self) -> LinkSnapshot:
        return LinkSnapshot(
            id=self.id,
            src=self.src.address,
            dst=self.dst.address,
            type=self.type.value,
            status=self.status,
            snr=self._json_safe_number(self.snr, -120.0),
            distance=self._json_safe_number(self.distance, 0.0),
            line_of_sight=self._json_safe_number(self.line_of_sight, 0.0),
            bandwidth=self._json_safe_number(self.bandwidth, 0.0),
            capacity=self._json_safe_number(self.capacity, 0.0),
        )
        
    def serialize(self) -> dict:
        return self.snapshot().model_dump()