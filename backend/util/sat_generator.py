from typing import List
import numpy as np
from skyfield.api import EarthSatellite, Time, wgs84, load

def generate_constellation(
        alt: float,        # m
        inc: float,        # deg
        P: int, 
        T: int, 
        F: float
    ) -> List[EarthSatellite]:
    """
    按Walker参数生成卫星列表（轨道高度单位：米）
    """
    R_EARTH = 6371000.0
    MU = 3.986004418e14  # 地球引力常数，单位：m^3/s^2
    
    satellites: List[EarthSatellite] = []
    num_ord = T // P  # 每个平面卫星数
    # 轨道半长轴a（米）
    a: float = R_EARTH + alt
    # 平均角速度 n（rad/s），MU 单位 m^3/s^2
    n: float = np.sqrt(MU / a**3)
    # mean_motion: revs/day，通常用于TLE等
    mean_motion: float = n * 86400.0 / (2 * np.pi)
    
    if abs(inc - 90.0) < 1e-3:
        raan_step = 180.0 / P
    else:
        raan_step = 360.0 / P
    for p in range(P):
        raan: float = raan_step * p  # 升交点赤经(度)
        
        for s in range(num_ord):
            id: int = p * num_ord + s
            name = f"{p:02d}-{s:02d}"
            
            # Walker星座相位角，度
            phase: float = (360.0 / num_ord) * s + (360.0 / T) * p * F
            
            # 保持在 [0, 360) 范围内
            phase = phase % 360.0
            sat = generate_satellite_model(
                id=id,                      # 卫星的ID
                name=name,                  # 卫星序列号=卫星名称
                inc=inc,                    # 倾角，度
                raan=raan,                  # 升交点赤经，度
                mean_anomaly=phase,         # 平近点角，度
                mean_motion=mean_motion,    # revs/day（如用skyfield）
            )
            
            satellites.append(sat)
    return satellites

def generate_satellite_model(
        id: int,
        name: str, 
        inc: float, 
        raan: float, 
        mean_anomaly: float, 
        mean_motion: float, 
        epoch_year=2020, 
        epoch_day=153.0, 
    ):
    """
    生成一个 EarthSatellite 对象的 TLE，近地点幅角、偏心率等参数使用默认或0值。
    """
    # TLE年份两位（2000以后）
    epoch_yy = epoch_year % 100
    epoch_str = f"{epoch_yy:02d}{epoch_day:012.8f}"
    # TLE字段
    inclination = f"{inc:8.4f}"
    raan_str = f"{raan:8.4f}"
    eccentricity = "0000000"      # 偏心率e=0，注意7位整数
    arg_perigee = "000.0000"      # 近地点幅角
    mean_anom = f"{mean_anomaly:8.4f}"
    mean_mot = f"{mean_motion:11.8f}"
    rev_number = "0"
    # 第1行
    line1_body = (
        f"1 {id:05d}U "
        f"{epoch_str} "
        f".00000000 "      # Mean motion dot
        f"00000-0 "        # Mean motion ddot
        f"00000+0 "        # B*
        f"0  999"
    )
    line1 = line1_body.ljust(68) + tle_checksum(line1_body)
    # 第2行
    line2_body = (
        f"2 {id:05d} "
        f"{inclination} "
        f"{raan_str} "
        f"{eccentricity} "
        f"{arg_perigee} "
        f"{mean_anom} "
        f"{mean_mot} "
        f"{rev_number:5s}"
    )
    line2 = line2_body.ljust(68) + tle_checksum(line2_body)
    return EarthSatellite(line1, line2, name)

def tle_checksum(line: str) -> str:
    total = 0
    for c in line[:68]:
        if c.isdigit():
            total += int(c)
        elif c == '-':
            total += 1
    return str(total % 10)