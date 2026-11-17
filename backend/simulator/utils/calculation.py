import math

def calc_fov(focal_length_mm: float, width_px: int, length_px: int, px_size_width: float, px_size_length: float):
    """
    计算相机宽和长方向的视场角（FOV），单位：度
    :param focal_length_mm: 焦距，mm
    :param width_px: 水平方向像素数
    :param length_px: 垂直方向像素数
    :param px_size_width: 水平方向像元尺寸，μm
    :param px_size_length: 垂直方向像元尺寸，μm
    :return: (fov_w, fov_l) 视场角（度）
    """
    # μm 转 mm
    sensor_w = width_px * px_size_width * 0.001
    sensor_l = length_px * px_size_length * 0.001
    fov_w = 2 * math.atan(sensor_w / (2 * focal_length_mm)) * 180 / math.pi
    fov_l = 2 * math.atan(sensor_l / (2 * focal_length_mm)) * 180 / math.pi
    return fov_w, fov_l
