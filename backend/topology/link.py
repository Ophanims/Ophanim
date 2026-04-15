import enum
import math
from typing import List
import numpy as np
from pydantic import BaseModel
from topology.node import Node
from controller.project_controller import ProjectBase
from entity.sat import Satellite
from entity.gs import GroundStation
from entity.process import Process
from util.const import R_EARTH

class Contact(BaseModel):
    info: BaseModel
    

class LinkType(enum.Enum):
    ISL = "ISL"  # 卫星间链路
    UL = "UL"  
    DL = "DL"  
    
    
class LinkSnapshot(BaseModel):
    id: str
    src: str
    dst: str
    type: str
    status: bool
    snr: float
    elevation_angle: float
    distance: float
    line_of_sight: float
    bandwidth: float
    carrier_frequency: float
    capacity: float
    loss: float
    antenna_gain_of_receive: float
    antenna_gain_of_transmit: float
    transmit_signal_power: float


class Link:
    """
    链路类：处理节点间的通信逻辑
    """

    def __init__(self, src: Node, dst: Node):
        self.id = f"({src.address},{dst.address})"
        self.src = src
        self.dst = dst
        self.type = LinkType.ISL          # ISL, SGL, TL
        self.status = False              # 是否连通
        
        self.MAX_PLANE = 0
        self.MAX_CONCURRENT_TRANSMISSION = 0
        
        # 物理参数
        self.snr = 0.0                   # 信噪比 (dB)
        self.elevation_angle = 0.0       # 仰角 (度)
        self.distance = 0.0              # m
        self.line_of_sight = 0.0         # m
        self.bandwidth = 20e6            # Hz (默认 20 MHz)
        self.carrier_frequency = 2e9     # Hz
        self.capacity = 0.0              # bps
        self.loss = 0.0
        self.antenna_gain_of_receive = 0.0 # dBi
        self.antenna_gain_of_transmit = 0.0 # dBi
        self.transmit_signal_power = 0.0 # W
        
        # 模拟
        self.processes: List[Process] = []  # 当前链路上正在进行的传输过程列表
        
    def setup(self, project: ProjectBase):
        self.MAX_PLANE = int(project.maximumNumberOfPlane or 0)
        self.MAX_CONCURRENT_TRANSMISSION = int(project.maximumConcurrentTransmission or 0)
        
        # 根据链路类型选择合适的频率和带宽参数
        if isinstance(self.src, Satellite) and isinstance(self.dst, Satellite):
            # ISL 链路使用 ISL 频率和带宽
            self.type = LinkType.ISL
            self.bandwidth = self.src.BANDWIDTH_OF_ISL * 1e6
            self.carrier_frequency = self.src.CARRIER_FREQUENCY_OF_ISL * 1e9
            self.antenna_gain_of_receive = self.dst.ANTENNA_GAIN_OF_ISL_RECEIVE
            self.antenna_gain_of_transmit = self.src.ANTENNA_GAIN_OF_ISL_TRANSMIT
            self.transmit_signal_power = self.src.transmit_signal_ISL_power
        elif isinstance(self.src, GroundStation) and isinstance(self.dst, Satellite):
            # 上行链路使用地面站的上行参数
            self.type = LinkType.UL
            self.bandwidth = self.src.BANDWIDTH_OF_UL * 1e6
            self.carrier_frequency = self.src.CARRIER_FREQUENCY_OF_UP * 1e9
            self.antenna_gain_of_receive = self.dst.ANTENNA_GAIN_OF_UL_RECEIVE
            self.antenna_gain_of_transmit = self.src.ANTENNA_GAIN_OF_UL_TRANSMIT
            self.transmit_signal_power = self.src.transmit_signal_UL_power
        elif isinstance(self.src, Satellite) and isinstance(self.dst, GroundStation):
            # 下行链路使用地面站的下行参数
            self.type = LinkType.DL
            self.bandwidth = self.src.BANDWIDTH_OF_DL * 1e6
            self.carrier_frequency = self.src.CARRIER_FREQUENCY_OF_DL * 1e9
            self.antenna_gain_of_receive = self.dst.ANTENNA_GAIN_OF_DL_RECEIVE
            self.antenna_gain_of_transmit = self.src.ANTENNA_GAIN_OF_DL_TRANSMIT
            self.transmit_signal_power = self.src.transmit_signal_DL_power

    def _sync_transmit_signal_power(self):
        if self.type == LinkType.ISL and isinstance(self.src, Satellite):
            self.transmit_signal_power = float(getattr(self.src, "transmit_signal_ISL_power", 0.0))
        elif self.type == LinkType.UL and isinstance(self.src, GroundStation):
            self.transmit_signal_power = float(getattr(self.src, "transmit_signal_UL_power", 0.0))
        elif self.type == LinkType.DL and isinstance(self.src, Satellite):
            self.transmit_signal_power = float(getattr(self.src, "transmit_signal_DL_power", 0.0))
        else:
            self.transmit_signal_power = 0.0

    def refresh(self):
        self._sync_transmit_signal_power()
        self.distance = self.calc_euclidean_distance()
        
        # 判断物理上是否连通 (视距)
        self.status = self.check_connectivity()
        
        if self.status:
            # 1. 先算基础损耗
            self.loss = self.calc_fspl_db() 
            # 2. 算 SNR (返回 dB)
            self.snr = self.calc_signal_to_noise_ratio() 
            # 3. 算实际数据吞吐量 capacity (bps)
            self.capacity = self.calc_capacity()
        else:
            self.loss = 9999.9
            # JSON 不支持 Infinity，使用有限的低 SNR 哨兵值。
            self.snr = -9999.9
            self.capacity = 0.0
            
    def is_available(self) -> bool:
        if len(self.processes) >= self.MAX_CONCURRENT_TRANSMISSION:
            return False
        
    def check_connectivity(self) -> bool:
        if isinstance(self.src, Satellite) and isinstance(self.dst, Satellite):
            
            plane_diff = abs(self.src.plane - self.dst.plane)
            order_diff = abs(self.src.order - self.dst.order)
            
            seam_con = plane_diff == self.MAX_PLANE - 1

            inter_link_con = plane_diff == 1 and order_diff == 0
                
            intra_link_con = plane_diff == 0
                
            if not inter_link_con and not intra_link_con or seam_con:
                return False
            
            # ISL 使用视距公式
            self.line_of_sight = self.calc_line_of_sight() 
            return self.distance < self.line_of_sight
        else:
            # 确保 theta >= 10
            self.elevation_angle = self.calc_elevation_angle()
            return self.elevation_angle >= 10.0
    
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
        # 传输天线增益 (dBi) 转线性增益
        G_tx = self.antenna_gain_of_transmit
        # 接收天线增益 (dBi) 转线性增益
        G_rx = self.antenna_gain_of_receive
        P_tx = self.transmit_signal_power
        # Boltzmann Constant (J/K)
        k = 1.380649e-23
        # System Noise Temperature (K)
        T = 290
        # Bandwidth (hz)
        B = max(self.bandwidth, 1.0)

        # 1. 发射端参数 (EIRP)
        EIRP = 10 * math.log10(max(P_tx, 1e-12)) + G_tx  # dBW, 加上发射天线增益
        
        # 2. 自由空间路径损耗 (FSPL)
        L_fs_db = self.calc_fspl_db()
        
        # # 3. 大气衰减
        # L_m = self.calc_attenuation_factor()
        # L_m_db = -10 * math.log10(L_m) if L_m > 0 else 0.0 
        
        # 4. 计算接收功率 (dBW)
        k_dbw = 10 * math.log10(k)  # dBW/K/Hz
        G_T = G_rx - 10 * math.log10(T)

        # 6. 计算 SNR (dB)
        snr_db = EIRP + G_T - L_fs_db - k_dbw - 10 * math.log10(B)
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
        else:
            return 0.8  # 地面链路有轻微衰减
        
    def calc_fspl_db(self) -> float:
        if self.distance <= 0:
            return 0.0
            
        c = 299792458.0  # 精确光速
        f = self.carrier_frequency
        d = self.distance
        
        # 线性公式: L_fs = (4 * pi * d * f / c)^2
        # 对数转换: 20 * log10(4 * pi * d * f / c)
        fspl_db = 20 * math.log10(4 * math.pi * d * f / c)
        
        return fspl_db
    
    def calc_elevation_angle(self) -> float:
        """计算地面站对卫星的仰角 (SGL 专用)"""
        # 确保 gs 是地面站，sat 是卫星
        gs = np.array(
            [self.src.x, self.src.y, self.src.z]
            if isinstance(self.src, GroundStation)
            else [self.dst.x, self.dst.y, self.dst.z],
            dtype=float,
        )
        sat = np.array(
            [self.src.x, self.src.y, self.src.z]
            if isinstance(self.src, Satellite)
            else [self.dst.x, self.dst.y, self.dst.z],
            dtype=float,
        )

        vec = sat - gs

        # 站星向量
        norm_vec = np.linalg.norm(vec)
        if norm_vec == 0:
            return 0.0
        gs_norm_norm = np.linalg.norm(gs)
        if gs_norm_norm == 0:
            return 0.0
        gs_norm = gs / gs_norm_norm
        elev_rad = np.arcsin(np.dot(vec, gs_norm) / norm_vec)
        elev_deg = np.degrees(elev_rad)

        return elev_deg

    def snapshot(self) -> LinkSnapshot:
        return LinkSnapshot(
            id=self.id,
            src=self.src.address,
            dst=self.dst.address,
            type=self.type.value,
            status=self.status,
            snr=self.snr,
            elevation_angle=self.elevation_angle,
            distance=self.distance,
            line_of_sight=self.line_of_sight,
            bandwidth=self.bandwidth,
            carrier_frequency=self.carrier_frequency,
            capacity=self.capacity,
            loss=self.loss,
            antenna_gain_of_receive=self.antenna_gain_of_receive,
            antenna_gain_of_transmit=self.antenna_gain_of_transmit,
            transmit_signal_power=self.transmit_signal_power,
        )
        
    def serialize(self) -> dict:
        return self.snapshot().model_dump()