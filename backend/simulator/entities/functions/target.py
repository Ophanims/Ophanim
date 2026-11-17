from simulator.utils.polygon import calculate_coverage, generate_square, latlon_to_xy
import numpy as np

def is_on_target(sub_lat, sub_lon, sl, v, roi_lat, roi_lon, roi_length):
    """
    判断卫星当前是否覆盖目标ROI
    :param sub_lat: 卫星地面投影纬度
    :param sub_lon: 卫星地面投影经度
    :param sl: 成像边长
    :param v: 成像方向角
    :param roi_lat: ROI中心纬度
    :param roi_lon: ROI中心经度
    :param roi_length: ROI边长
    :return: bool
    """
    # 坐标平移到 ROI 为原点的局部坐标系
    sub_xy = latlon_to_xy(sub_lat, sub_lon, roi_lat, roi_lon)
    roi_xy = (0.0, 0.0)
    image_poly = generate_square(sub_xy, sl, v)
    roi_poly = generate_square(roi_xy, roi_length)
    coverage = calculate_coverage(image_poly, roi_poly)
    return coverage > 0.9


def is_on_station(gs_ecef: np.ndarray, sat_ecef: np.ndarray, min_elevation_deg: float = 15.0) -> bool:
    """
    判断地面站是否能看到卫星
    参数:
        gs_ecef: 地面站 ECEF 坐标 (3,)
        sat_ecef: 卫星 ECEF 坐标 (3,)
    返回:
        True 表示仰角大于 15 度
    """
    vec = sat_ecef - gs_ecef
    vec_unit = vec / np.linalg.norm(vec)
    gs_unit = gs_ecef / np.linalg.norm(gs_ecef)

    # 计算仰角（Elevation）= arcsin(单位视线向量 与 地面站位置向量的夹角余弦)
    cos_angle = np.dot(vec_unit, gs_unit)
    elevation_rad = np.arcsin(cos_angle)
    elevation_deg = np.degrees(elevation_rad)

    return elevation_deg > min_elevation_deg



