import math
from typing import List
import uuid
import numpy as np
from simulator.config import MU, R_EARTH  # 均为“米”单位
from simulator.models.satellite_model import SatelliteModel
from simulator.utils.generator import generate_satellite_model

class ConstellationModel:
    def __init__(
        self,
        number_of_planes: int,           # 轨道面数（int）
        number_of_sat_per_planes: int,       # 每轨道面卫星数（int）
        altitude: float,           # 轨道高度，单位：米
        inclination_deg: float,    # 轨道倾角，单位：度
        phase_factor: int,          # 相位阶差因子
        id: str = "None",
        name: str = "None",
    ):
        self.id = id
        self.name = name
        self.number_of_planes = number_of_planes
        self.number_of_sat_per_planes = number_of_sat_per_planes
        self.altitude = altitude
        self.inclination_deg = inclination_deg
        self.phase_factor = phase_factor

        self._satellites = self.generate_constellation()

    @property
    def satellites(self) -> List[SatelliteModel]:
        return self._satellites

    @satellites.setter
    def satellites(self, sats: List[SatelliteModel]):
        if not all(isinstance(s, SatelliteModel) for s in sats):
            raise ValueError("All items must be Satellite instances.")
        self._satellites = sats

    def generate_constellation(self) -> List[SatelliteModel]:
        """
        按Walker参数生成卫星列表（轨道高度单位：米）
        """
        satellites: List[SatelliteModel] = []

        # 轨道半长轴a（米）
        a: float = R_EARTH + self.altitude

        # 平均角速度 n（rad/s），MU 单位 m^3/s^2
        n: float = np.sqrt(MU / a**3)

        # （可选）mean_motion: revs/day，通常用于TLE等
        mean_motion: float = n * 86400.0 / (2 * np.pi)

        if abs(self.inclination_deg - 90.0) < 1e-3:
            raan_step = 180.0 / self.number_of_planes
        else:
            raan_step = 360.0 / self.number_of_planes

        for p in range(self.number_of_planes):
            raan: float = raan_step * p  # 升交点赤经(度)
            for s in range(self.number_of_sat_per_planes):
                # Walker星座相位角，度
                phase: float = (
                    360.0 * ((s + self.phase_factor * p) % self.number_of_sat_per_planes)
                    / self.number_of_sat_per_planes
                )
                satnum: int = p * self.number_of_sat_per_planes + s
                serial = f"{self.name}-{p:02d}-{s:02d}"

                sat = generate_satellite_model(
                    id=serial,                  # 卫星的ID
                    satnum=satnum,              # 卫星的星座序数代号
                    order=s,                    # 卫星的平面序数代号
                    plane=p,                    # 卫星的平面代号
                    serial=serial,              # 卫星序列号=卫星名称
                    inc=self.inclination_deg,   # 倾角，度
                    raan=raan,                  # 升交点赤经，度
                    mean_anomaly=phase,         # 平近点角，度
                    mean_motion=mean_motion,    # revs/day（如用skyfield）
                    altitude=self.altitude,     # 轨道高度，米
                )

                satellites.append(sat)
        return satellites

    @staticmethod
    def from_dict(co: dict):
        return ConstellationModel(
            id=co.id if co.id else uuid.uuid4().hex,
            name=co.name,
            number_of_planes=co.number_of_planes,
            number_of_sat_per_planes=co.number_of_sat_per_planes,
            altitude=co.altitude,
            inclination_deg=co.inclination,
            phase_factor=co.phase_factor,
        )

