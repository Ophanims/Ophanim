import math
from typing import List, Optional, Tuple
from pyproj import Geod
GEOD = Geod(ellps="WGS84")

class CameraModel:
    """
    摄像头类，表示一个摄像头的经纬度位置。
    """
    def __init__(self,
        width_px: int = 1920,
        length_px: int = 1080,
        px_size_width: float = 0.01,
        px_size_length: float = 0.01,
        focal_length_mm: float = 50.0,
        channels_per_pixel: int = 3,
        bits_per_channel: int = 8
    ):
        self.width_px = width_px
        self.length_px = length_px
        self.px_size_width = px_size_width
        self.px_size_length = px_size_length
        self.focal_length_mm = focal_length_mm
        self.channels_per_pixel = channels_per_pixel
        self.bits_per_channel = bits_per_channel
        self.fov_w = self._fov_w()  # 视场角宽度（度）
        self.fov_l = self._fov_l()
        self.data_size_bit = self._data_size_bit()  # 每张图像数据大小（位）

    def _fov_w(self):
        sensor_w = self.width_px * self.px_size_width * 0.001
        fov_w = 2 * math.atan(sensor_w / (2 * self.focal_length_mm)) * 180 / math.pi
        return fov_w

    def _fov_l(self):
        sensor_l = self.length_px * self.px_size_length * 0.001
        fov_l = 2 * math.atan(sensor_l / (2 * self.focal_length_mm)) * 180 / math.pi
        return fov_l

    def _data_size_bit(self) -> float:
        data_size = self.width_px * self.length_px * self.channels_per_pixel * self.bits_per_channel
        return data_size

    def calc_swath_length(self, altitude: float) -> float:
        fov_rad = math.radians(self.fov_l)
        swath_length = 2 * altitude * math.tan(fov_rad / 2)
        return swath_length

    def calc_swath_width(self, altitude: float) -> float:
        fov_rad = math.radians(self.fov_w)
        swath_width = 2 * altitude * math.tan(fov_rad / 2)
        return swath_width

    def coverage_corners(self, altitude: float, lon: float, lat: float, angle: float) -> List[Tuple[float, float]]:
        if abs(lat) > 90:
            raise ValueError("Latitude must be between -90 and 90 degrees")

        half_w = self.calc_swath_width(altitude) / 2
        half_l = self.calc_swath_length(altitude) / 2

        # 角点相对中心的方向（NE, NW, SW, SE）
        offsets = [
            (half_l, half_w),   # NE
            (half_l, -half_w),  # NW
            (-half_l, -half_w), # SW
            (-half_l, half_w),  # SE
        ]
        corners = []
        for dy, dx in offsets:
            # 计算角点的方位角和距离
            az = (math.degrees(math.atan2(dx, dy)) + angle) % 360
            dist = math.sqrt(dx**2 + dy**2)
            lon_out, lat_out, _ = GEOD.fwd(lon, lat, az, dist)
            lon_out = ((lon_out + 180) % 360) - 180
            corners.append((lat_out, lon_out))
        return corners

    @staticmethod
    def from_dict(hardware: dict):
        return CameraModel(
            width_px = hardware.width_px,
            length_px = hardware.length_px,
            px_size_width = hardware.px_size_width,
            px_size_length = hardware.px_size_length,
            focal_length_mm = hardware.focal_length_mm,
            channels_per_pixel = hardware.channels_per_pixel,
            bits_per_channel = hardware.bits_per_channel
        )
