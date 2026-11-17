import numpy as np
from simulator.entities._satellite_modules.constants import BATTERY_CAPACITY, BATTERY_THRESHOLD
from simulator.schemas.base import XYZ


# class EnergyModule:

#     def _execute(self, energy_needed: float):
#         # 优先使用太阳能
#         solar_energy = min(self.et, energy_needed)
#         self.s_t += solar_energy
#         self.et -= solar_energy

#         # 使用电池补充剩余能量
#         remaining = energy_needed - solar_energy
#         battery_energy = self.B_t * BATTERY_CAPACITY
#         battery_used = min(battery_energy, remaining)
#         self.b_t = battery_used
#         self.B_t -= battery_used / BATTERY_CAPACITY

def equa_solar_income(dt: float, sat_pos: XYZ, dimensions: tuple[float, float, float],
                    solar_vector: np.ndarray, velocity: np.ndarray, mu_t: int) -> float:
    """
    计算dt秒内，总太阳能电量（Wh），基于论文模型求和6面功率。
    :param dt: 持续时间（单位：秒，s）
    :param sat_pos: 卫星空间中心位置坐标（XYZ类型，x, y, z单位：米，m）
    :param dimensions: 卫星立方体尺寸 (length, width, height)（单位：米，m）
    :param solar_vector: 单位太阳向量（无量纲，单位向量）
    :param velocity: 单位飞行方向向量（无量纲，单位向量）
    :param mu_t: 光照指示器（1为阳光区，0为阴影区，无量纲）
    :return: 发电量（单位：瓦时，Wh）
    """
    efficiency: float = 0.30   # 微型卫星GaAs电池效率（无量纲）
    solar_constant: float = 1366  # 太阳常数（单位：W/m²）

    # 转换为np.array（单位：m）
    sat_pos_array = np.array([sat_pos.x, sat_pos.y, sat_pos.z])  # 单位：m

    # 计算zenith (+x: 远离地球方向，单位向量，无量纲)
    zenith = sat_pos_array / np.linalg.norm(sat_pos_array)

    # 使用单位速度向量（-z方向，无量纲）
    unit_velocity = velocity / np.linalg.norm(velocity)  # 确保单位化

    # y方向：右手系，cross(zenith, unit_velocity)（无量纲）
    y_dir = np.cross(zenith, unit_velocity)
    unit_y = y_dir / np.linalg.norm(y_dir)

    # 6面法向（论文坐标系：+x=zenith, -z=unit_velocity, y=unit_y，无量纲）
    normals = [
        zenith,          # +x
        -zenith,         # -x
        unit_y,          # +y
        -unit_y,         # -y
        np.cross(unit_velocity, zenith),  # +z
        unit_velocity    # -z
    ]

    # 面面积（单位：m²）
    length, width, height = dimensions  # 单位：m
    areas = [
        width * height,  # +x/-x，单位：m²
        width * height,  # +x/-x
        length * height, # +y/-y
        length * height, # +y/-y
        length * width,  # +z/-z
        length * width   # +z/-z
    ]

    # 总瞬时功率（单位：W）
    total_power = 0.0
    for i, normal in enumerate(normals):
        unit_normal = normal / np.linalg.norm(normal)  # 单位向量，无量纲
        cos_phi = np.dot(solar_vector, unit_normal)  # cos(φ)，无量纲
        if cos_phi > 0:
            p_max = areas[i] * efficiency * solar_constant  # 单位：m² * 无量纲 * W/m² = W
            total_power += p_max * cos_phi  # 单位：W

    total_power *= mu_t  # 阴影区功率=0（无量纲）

    # dt秒内电量（单位：Wh）
    charge_amount = total_power * dt  # 单位：Energy (J)=Energy (Wh)×3600
    return max(charge_amount, 0)  # 单位：J

#     def _equa_simple_energy(self, power: float, dt: float) -> float:
#         """
#         计算dt秒内，某功率持续工作的耗电量（Wh）
#         :param power: 功率 （单位：W）
#         :param dt: 持续时间（单位：秒）
#         :return: 消耗电量（单位：Wh）
#         """
#         discharge_amount = power * dt / 3600
#         return discharge_amount

#     def calculate_proc_rate(self, rho: float = 20, epsilon: float = 0.1, N_CPU: int = 4, f_k: float = 1.8e9) -> float:
#         """
#         计算处理速率 (bits/s), 基于公式 (5): rate = N_CPU * f_k / C(rho, epsilon)。
#         来源: [1] Section II.B Processing (PAGE 8, equation (5)).
#         :param rho: 压缩比 (rho > 1, e.g., 2-10)
#         :param epsilon: 复杂度常数 (cycles/bit, e.g., 0.1)
#         :param N_CPU: CPU核数 (默认4オープ4, [1] Table II PAGE 23)
#         :param f_k: CPU频率 (Hz, 默认1.8e9, [1] Table II PAGE 23)
#         :return: 处理速率 (bits/s)
#         """
#         C_rho = np.exp(epsilon * rho) - np.exp(epsilon)  # cycles/bit, [1] equation after (7) PAGE 8
#         rate = N_CPU * f_k / C_rho if C_rho > 0 else 0  # bits/s, derived from [1] equation (5) PAGE 8
#         return rate

#     def calculate_proc_energy(self, D_k: float, rho: float = 20, epsilon: float = 0.1, f_k: float = 1.8e9, P_proc_max: float = 10.0) -> float:
#         """
#         计算处理能耗 (Wh), 基于论文公式 (11): E_proc = D_k * C(rho, epsilon) * E_cycle。
#         来源: [1] Section II.E Energy consumption (PAGE 9, equation (11)).
#         :param D_k: 数据大小 (MBs, e.g., 100 MB)
#         :param rho: 压缩比 (rho >1)
#         :param epsilon: 复杂度常数 (cycles/bit)
#         :param f_k: CPU频率 (Hz, 默认1.8e9, [1] Table II PAGE 23)
#         :param N_CPU: CPU核数 (默认4, [1] Table II PAGE 23)
#         :param P_proc_max: 最大处理功耗 (W, 默认10, [1] Table II PAGE 23)
#         :return: 能耗 (Wh)
#         """
#         f_CPU: float = 1.8e9  # 最大频率 (Hz, [1] Table II PAGE 23)
#         u: float = P_proc_max / f_CPU**3  # 有效电容系数 (J/Hz²/cycle), [1] equation (10) PAGE 9
#         E_cycle = u * f_k**2  # J/cycle, [1] equation (10) PAGE 9
#         C_rho = np.exp(epsilon * rho) - np.exp(epsilon)  # cycles/bit, [1] equation after (7) PAGE 8
#         E_proc = D_k * C_rho * E_cycle  # J, [1] equation (11) PAGE 9
#         discharge_amount = E_proc / 3600  # Wh
#         return max(discharge_amount, 0)

#     def calculate_rf_energy(self, data_bits: float, rate_bps: float, mu_RF_amp: float = 1.0, P_RF_tx: float = 10.0, P_RF_static: float = 0.0) -> float:
#         """
#         计算RF链路 (uplink/downlink) 时隙内能耗 (Wh), 基于论文 [1] Section II.E equation (10) (PAGE 9), D_k / R_k = dt。
#         :param dt: 时隙持续时间 (s)
#         :param mu_RF_amp: RF功放器效率因子 (默认1, [1] Table II PAGE 23)
#         :param P_RF_tx: RF传输功率 (W, 默认10 for downlink, 5 for uplink, [1] Table II PAGE 23)
#         :param P_RF_static: RF静态功耗 (W, 默认0)
#         :return: 时隙能耗 (Wh)
#         """
#         P_RF = mu_RF_amp * P_RF_tx + P_RF_static  # 总功率 (W)
#         E_RF_trans = P_RF * data_bits / rate_bps
#         discharge_amount = E_RF_trans / 3600  # Wh
#         return max(discharge_amount, 0)

#     def calculate_isl_energy(self, data_bits: float, rate_bps: float, mu_ISL_amp: float = 1.0, P_ISL_tx: float = 60.0, P_ISL_static: float = 0.0) -> float:
#         """
#         计算FSO ISL链路时隙内能耗 (Wh), 基于论文 [1] Section II.E equation (9) (PAGE 9), D_k / R_k = dt。
#         :param dt: 时隙持续时间 (s)
#         :param mu_ISL_amp: FSO传输效率参数 (默认0.1, [1] equation (8) PAGE 9, Table II PAGE 23)
#         :param P_ISL_tx: RF传输功率
#         :param P_ISL_static: ISL静态功耗 (W, 默认0)
#         :return: 时隙能耗 (Wh)
#         """
#         P_ISL = mu_ISL_amp * P_ISL_tx + P_ISL_static
#         eta = mu_ISL_amp * P_ISL_tx / P_ISL
#         E_ISL_trans = eta * P_ISL * data_bits / rate_bps
#         discharge_amount = E_ISL_trans / 3600  # Wh
#         return max(discharge_amount, 0)


