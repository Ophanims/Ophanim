import math
from typing import List, Tuple
from pyproj import Transformer
from shapely.geometry import Polygon

from simulator.config import R_EARTH  # 地球半径，单位为米（通常为 6371000）

# def to_geodetic(coords):
#     transformer_to_latlon = Transformer.from_crs("EPSG:6933", "EPSG:4326", always_xy=True)
#     return [transformer_to_latlon.transform(x, y) for x, y in coords]

# def to_projected(coords):
#     transformer_to_m = Transformer.from_crs("EPSG:4326", "EPSG:6933", always_xy=True)
#     return [transformer_to_m.transform(lon, lat) for lon, lat in coords]

def clip_by_inc(region, inc):
    """
    根据轨道倾角裁剪纬度范围。
    region: ((min_lat, max_lat), (min_lon, max_lon))
    inc: 倾角（度），裁剪后纬度为 [max(min_lat, -inc), min(max_lat, inc)]
    返回：((裁剪后纬度范围), (经度范围))
    """
    (min_lat, max_lat), lon_range = region
    clipped_min_lat = max(min_lat, -inc)
    clipped_max_lat = min(max_lat, inc)
    return ((clipped_min_lat, clipped_max_lat), lon_range)

def latlon_to_xy(
    lat: float,
    lon: float,
    center_lat: float,
    center_lon: float
) -> Tuple[float, float]:
    """
    将经纬度坐标 (lat, lon) 转换为以 center_lat, center_lon 为原点的局部二维直角坐标系坐标（单位：米）

    参数：
    - lat: 点的纬度（单位：度）
    - lon: 点的经度（单位：度）
    - center_lat: 局部坐标原点的纬度
    - center_lon: 局部坐标原点的经度

    返回：
    - (x, y): 东西向和南北向距离，单位为米
    """
    delta_lat = math.radians(lat - center_lat)
    delta_lon = math.radians(lon - center_lon)
    x = R_EARTH * delta_lon * math.cos(math.radians(center_lat))  # 东西方向（米）
    y = R_EARTH * delta_lat  # 南北方向（米）
    return (y, x)


def generate_square(
    center_xy: Tuple[float, float],
    length: float,
    angle_deg: float = 0
) -> List[Tuple[float, float]]:
    """
    以中心点为中心，生成一个边长为 length、顺时针旋转 angle_deg 的正方形四个顶点（局部坐标系）

    参数：
    - center_xy: 中心点坐标 (x, y)，单位：米
    - length: 正方形边长
    - angle_deg: 正方形绕中心旋转角度（地面速度方向），单位：度（从正东为0度逆时针）

    返回：
    - List[Tuple[float, float]]: 顺时针四角点坐标
    """
    cx, cy = center_xy
    r = length / 2
    theta = math.radians(angle_deg)
    cos_theta = math.cos(theta)
    sin_theta = math.sin(theta)

    # 正方形顶点（以中心为原点，逆时针方向）
    corners = [
        (-r, -r),
        (r, -r),
        (r, r),
        (-r, r),
    ]

    # 旋转 + 平移
    rotated = [
        (
            cx + x * cos_theta - y * sin_theta,
            cy + x * sin_theta + y * cos_theta
        )
        for x, y in corners
    ]
    return rotated



def calculate_coverage(
    image_poly: List[Tuple[float, float]],
    roi_poly: List[Tuple[float, float]]
) -> float:
    """
    计算图像覆盖区域与 ROI 的重叠面积占 ROI 面积的百分比（单位：0~1）

    参数：
    - image_poly: 成像区域的四边形顶点坐标
    - roi_poly: ROI 区域的四边形顶点坐标

    返回：
    - float: 覆盖率（0~1）
    """
    poly_image = Polygon(image_poly)
    poly_roi = Polygon(roi_poly)

    if not poly_image.is_valid or not poly_roi.is_valid:
        return 0.0

    inter_area = poly_image.intersection(poly_roi).area
    roi_area = poly_roi.area
    return inter_area / roi_area if roi_area > 0 else 0.0
