import math
import numpy as np
from skyfield.api import EarthSatellite, Time, wgs84, load
from pyproj import Geod
GEOD = Geod(ellps="WGS84")

from simulator.config import R_EARTH
from simulator.config import EPHEMERIS
from simulator.models.camera_model import CameraModel
from simulator.schemas.base import XYZ, LatLon

TS = load.timescale()

class SatelliteModel():
    def __init__(self,
        altitude: float = 500e3,
        id: str = "None",
        order: int = 0,
        plane: int = 0,
        tle1text: str = "",
        tle2text: str = "",
    ):
        self.id = id
        self.motion = EarthSatellite(line1=tle1text, line2=tle2text, name=id, ts=TS)
        self.altitude = altitude
        self.inc = self.motion.model.inclo
        self.op = self._op()  # 轨道周期（秒）
        self.order = order
        self.plane = plane
        self.tle1text = tle1text
        self.tle2text = tle2text
        self.sub_loc = LatLon(lat=0.0, lon=0.0)
        self.pos = XYZ(x=0.0, y=0.0, z=0.0 )
        self.gva = 0.0  # ground track velocity azimuth 地面轨迹方向角
        self.is_sunlit = False

        self.camera = CameraModel()

    def locate(self, t) -> None:
        g1 = self.motion.at(t)
        subpoint = g1.subpoint()
        lat = subpoint.latitude.degrees
        lon = subpoint.longitude.degrees
        self.sub_loc = LatLon(lat=lat, lon=lon)
        xyz = g1.position.m
        self.pos = XYZ(x=xyz[0], y=xyz[1], z=xyz[2])
        self._gva(t)
        self.is_sunlit = g1.is_sunlit(EPHEMERIS)

    def _gva(self, t: Time) -> float:
        t2 = t + self._ts() / 86400.0
        g2 = self.motion.at(t2)
        subpoint2 = g2.subpoint()
        lat2 = subpoint2.latitude.degrees
        lon2 = subpoint2.longitude.degrees
        az12, az21, dist = GEOD.inv(self.sub_loc.lon, self.sub_loc.lat, lon2, lat2)
        self.gva = az12 % 360

    def capture(self):
        angle = self.gva if self.gva is not None else 0.0
        corners = self.camera.coverage_corners(self.altitude, self.sub_loc.lon, self.sub_loc.lat, angle)
        return corners

    def _op(self):
        period_minutes = 2 * np.pi / self.motion.model.no_kozai
        period = period_minutes * 60
        return period

    def _ts(self):
        l_s = self.camera.calc_swath_length(self.altitude)
        t_slot = self.op / np.ceil(R_EARTH * 2 * np.pi / l_s)
        return t_slot



