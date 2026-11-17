import numpy as np
from skyfield.api import wgs84
from pyproj import Geod
GEOD = Geod(ellps="WGS84")

from simulator.schemas.base import XYZ, LatLon


class ROIModel:
    def __init__(self,
        lat: float,
        lon: float,
        length: float,
        width: float,
        id: str = "None",
    ):
        self.id = id
        self.length = length
        self.width = length if width is None else width
        self.loc = LatLon(lat=lat, lon=lon)
        self.pos = XYZ(x=0.0, y=0.0, z=0.0)
        self.corners_pos = None
        self.corners_loc = None

    BASE_AZI = np.array([45, 135, 225, 315])

    def locate(self, t):
        topo = wgs84.latlon(self.loc.lat, self.loc.lon)
        g = topo.at(t)
        self.pos = XYZ(x=g.position.m[0], y=g.position.m[1], z=g.position.m[2])

        # 以 ROI 中心为起点，按 NE, NW, SW, SE 顺序计算四角
        half_len = self.length / 2.0
        half_wid = self.width / 2.0

        # offsets (dy north, dx east) 对应 NE, NW, SW, SE
        offsets = [
            (half_len, half_wid),    # NE
            (half_len, -half_wid),   # NW
            (-half_len, -half_wid),  # SW
            (-half_len, half_wid),   # SE
        ]

        azs = []
        dists = []
        for dy, dx in offsets:
            # arctan2(dx, dy) -> 方位角（度），dx 为东，dy 为北
            az = (np.degrees(np.arctan2(dx, dy))) % 360
            dist = np.hypot(dx, dy)
            azs.append(az)
            dists.append(dist)

        # 用大地正算得到四角的经纬（单位：度，距离单位与 length/width 一致，通常为米）
        lon_out, lat_out, _ = GEOD.fwd(
            np.full(4, self.loc.lon), np.full(4, self.loc.lat), azs, dists
        )
        lon_out = ((lon_out + 180) % 360) - 180

        # 保存角点经纬（lat, lon）和对应 ECEF 坐标
        self.corners_loc = np.column_stack((lat_out, lon_out))

        # corners_pos: 对每个角点在时间 t 的 ECEF 坐标（若 t 为序列，则为 (3,N)；stack 后为 (4,3,N)）
        corner_positions = []
        for lat_c, lon_c in zip(lat_out, lon_out):
            cp = wgs84.latlon(lat_c, lon_c).at(t).position.m
            corner_positions.append(cp)
        self.corners_pos = np.stack(corner_positions, axis=0)
