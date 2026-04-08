import math

import numpy as np
from backend.model.node import Node

class Link:
    """
    链路类：处理节点间的通信逻辑
    """
    def __init__(self, src: Node, dst: Node):
        self.src = src
        self.dst = dst
        self.type = "unknown"            # ISL, SGL, TL
        self.status = False              # 是否连通
        
        # 物理参数
        self.snr = 0.0                   # 信噪比 (dB)
        self.distance = 0.0              # m
        self.line_of_sight = 0.0         # m
        self.bandwidth = 20e6            # Hz (默认 20 MHz)
        self.capacity = 0.0              # bps

    def update_metrics(self):
        self.type = self.getType()
        
        # 判断物理上是否连通 (视距)
        self.status = self.check_connectivity()
        
        if self.status:
            # 1. 先算基础损耗
            self.loss = self.calc_fspl() 
            # 2. 算 SNR (返回 dB)
            self.snr = self.calc_signal_to_noise_ratio() 
            # 3. 算实际数据吞吐量 capacity (bps)
            self.data_rate = self.calc_capacity() 
        else:
            self.loss = float('inf')
            self.snr = float('-inf')
            self.data_rate = 0.0
            
    def getType(self) -> str:
        if self.src.__class__.__name__ == "Satellite" \
            and self.dst.__class__.__name__ == "Satellite":
            # inter-satellite link
            return "ISL"
        elif self.src.__class__.__name__ == "GroundStation" \
            and self.dst.__class__.__name__ == "GroundStation":
            # terrestrial link
            return "TL"
        else:
            # satellite-ground link
            return "SGL"
        
    def check_connectivity(self) -> bool:
        self.distance = self.calc_euclidean_distance()

        if self.type == "SGL":
            # 确保 theta >= 10
            return self.calc_elevation_angle() >= 10.0
        else:
            # ISL 使用视距公式
            self.line_of_sight = self.calc_line_of_sight()
            return self.distance < self.line_of_sight
    
    def calc_line_of_sight(self) -> float:
        """计算两节点间的视距"""
        R_EARTH = 6371000.0
        
        s = self.src.geographic_coordinates
        d = self.dst.geographic_coordinates
        
        s_alt = s['alt']
        d_alt = d['alt']

        return (math.sqrt(s_alt * (2 * R_EARTH + s_alt)) + 
            math.sqrt(d_alt * (2 * R_EARTH + d_alt)))
    
    def calc_euclidean_distance(self) -> float:
        """计算两节点间的欧氏距离"""
        s = self.src.cartesian_coordinates
        d = self.dst.cartesian_coordinates

        s_vec = np.array([s['x'], s['y'], s['z']], dtype=float)
        d_vec = np.array([d['x'], d['y'], d['z']], dtype=float)
        
        return float(np.linalg.norm(s_vec - d_vec))
    
    def calc_signal_to_noise_ratio(self) -> float:
        """计算信噪比 (SNR)，单位 dB"""
        # 1. 发射端参数 (EIRP)
        tx_power_dbw = 10 * math.log10(self.src.transmit_signal_power) # 假设输入是 W
        tx_gain_dbi = self.src.transmit_antenna_gain # 假设已经是 dBi
        eirp = tx_power_dbw + tx_gain_dbi

        # 2. 空间损耗
        fspl_db = self.calc_fspl() # 例如 150 dB
        
        # 3. 大气衰减 (dB)
        # 你的 calc_attenuation_factor 返回的是线性系数 (0.8)，这里转成 dB 损耗
        af_linear = self.calc_attenuation_factor()
        atm_loss_db = -10 * math.log10(af_linear) if af_linear > 0 else 0 

        # 4. 接收端功率 (dBW)
        rx_gain_dbi = self.dst.receive_antenna_gain
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
        if self.type == "ISL":
            return 1.0  # 卫星间无大气衰减
        elif self.type == "SGL":
            return 0.8  # 卫星-地面链路有一定衰减
        else:
            return 0.9  # 地面链路有轻微衰减
        
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
        gs = self.src if self.src.__class__.__name__ == "GroundStation" else self.dst
        sat = self.dst if self.src.__class__.__name__ == "GroundStation" else self.src

        p_gs = np.array([gs.cartesian_coordinates['x'], gs.cartesian_coordinates['y'], gs.cartesian_coordinates['z']])
        p_sat = np.array([sat.cartesian_coordinates['x'], sat.cartesian_coordinates['y'], sat.cartesian_coordinates['z']])

        # 站星向量
        r_gs_sat = p_sat - p_gs
        # 地面站法向量 (简化处理，指向地心反方向)
        n_gs = p_gs / np.linalg.norm(p_gs)

        # 计算仰角
        sin_el = np.dot(r_gs_sat, n_gs) / np.linalg.norm(r_gs_sat)
        return math.degrees(math.asin(max(-1.0, min(1.0, sin_el))))

    def get_state(self) -> dict:
        return {
            "id": f"({self.src.id},{self.dst.id})",
            "src": self.src.id,
            "dst": self.dst.id,
            "type": self.type,
            "status": self.status,
            "snr": round(self.snr, 2),
            "loss": round(self.loss, 2),
            "distance": round(self.distance, 2),
            "capacity": round(self.data_rate, 2),
        }