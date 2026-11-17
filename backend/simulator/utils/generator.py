import itertools
import random
from typing import Callable, Dict, List, Optional, Tuple, TypeVar
from skyfield.api import load

from simulator.models.satellite_model import SatelliteModel
# from old_models.satellite import Satellite
TS = load.timescale()

def generate_random_location(
    lat_range: Tuple[float, float] = (-90, 90),
    lon_range: Tuple[float, float] = (-180, 180),
    rng: Optional[random.Random] = None
) -> Tuple[float, float]:
    """
    Generate a random geographic coordinate (latitude, longitude) within the specified range.
    """
    rng = rng or random
    lat = rng.uniform(*lat_range)
    lon = rng.uniform(*lon_range)
    return lat, lon

def generate_random_location_set(
    n: int,
    lat_range: Tuple[float, float] = (-90, 90),
    lon_range: Tuple[float, float] = (-180, 180),
    rng: Optional[random.Random] = None
) -> list:
    """
    Generate a set of random geographic coordinates within the specified range.
    """
    return [generate_random_location(lat_range, lon_range, rng) for _ in range(n)]

T = TypeVar('T')

def generate_object_pool(
    band_n: List[int],
    band_region: List[Tuple[Tuple[float, float], Tuple[float, float]]] = [((-90, 90), (-180, 180))],
    make_object: Callable[..., T] = None,
    object_args: Optional[dict] = None,
    seed: Optional[int] = None
) -> Tuple[List[T], Dict[Tuple[int, Tuple[float, float], Tuple[float, float]], List[T]]]:
    """
    General object pool generator function, with optional seed for reproducibility.
    """
    # Set up local random generator if seed provided, otherwise use global random
    rng = random.Random(seed) if seed is not None else random

    if object_args is None:
        object_args = {}

    max_n = max(band_n)
    all_locations = {}

    for lat_range, lon_range in band_region:
        key = (lat_range, lon_range)
        locations = generate_random_location_set(max_n, lat_range, lon_range, rng)
        all_locations[key] = locations

    pool_list: List[T] = []
    pool_dict: Dict[Tuple[int, Tuple[float, float], Tuple[float, float]], List[T]] = {}

    cases = list(itertools.product(band_n, band_region))
    count = 0

    for n, (lat_range, lon_range) in cases:
        key = (lat_range, lon_range)
        coords = all_locations[key][:n]
        objs = []
        for i, (lat, lon) in enumerate(coords):
            obj_id = f"{make_object.__name__}-{key}-{i+1:02d}"
            obj = make_object(lat, lon, id=obj_id, **object_args)
            objs.append(obj)
            count += 1
        pool_list.extend(objs)
        pool_dict[(n, lat_range, lon_range)] = objs

    return pool_list, pool_dict


# def generate_satellite(
#     satnum: int,
#     plane: int,
#     order: int,
#     serial: str,
#     inc: float,
#     raan: float,
#     mean_anomaly: float,
#     mean_motion: float,
#     fov_w: float,
#     fov_l: float,
#     altitude: float,
#     epoch_year=2020,
#     epoch_day=153.0,
#     id = "None",
#     ):
#     """
#     生成一个 EarthSatellite 对象的 TLE，近地点幅角、偏心率等参数使用默认或0值。
#     """
#     # TLE年份两位（2000以后）
#     epoch_yy = epoch_year % 100
#     epoch_str = f"{epoch_yy:02d}{epoch_day:012.8f}"

#     # TLE字段
#     inclination = f"{inc:8.4f}"
#     raan_str = f"{raan:8.4f}"
#     eccentricity = "0000000"      # 偏心率e=0，注意7位整数
#     arg_perigee = "000.0000"      # 近地点幅角
#     mean_anom = f"{mean_anomaly:8.4f}"
#     mean_mot = f"{mean_motion:11.8f}"
#     rev_number = "0"

#     # 第1行
#     line1_body = (
#         f"1 {satnum:05d}U "
#         f"{epoch_str} "
#         f".00000000 "      # Mean motion dot
#         f"00000-0 "        # Mean motion ddot
#         f"00000+0 "        # B*
#         f"0  999"
#     )
#     line1 = line1_body.ljust(68) + tle_checksum(line1_body)

#     # 第2行
#     line2_body = (
#         f"2 {satnum:05d} "
#         f"{inclination} "
#         f"{raan_str} "
#         f"{eccentricity} "
#         f"{arg_perigee} "
#         f"{mean_anom} "
#         f"{mean_mot} "
#         f"{rev_number:5s}"
#     )
#     line2 = line2_body.ljust(68) + tle_checksum(line2_body)

#     return Satellite(
#         id=id,
#         order=order,
#         plane=plane,
#         name=serial,
#         line1=line1,
#         line2=line2,
#         ts=TS,
#         fov_l=fov_l,
#         fov_w=fov_w,
#         altitude=altitude,
#         tle1text=line1,
#         tle2text=line2
#     )

def generate_satellite_model(
    satnum: int,
    plane: int,
    order: int,
    serial: str,
    inc: float,
    raan: float,
    mean_anomaly: float,
    mean_motion: float,
    altitude: float,
    epoch_year=2020,
    epoch_day=153.0,
    id = "None",
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
        f"1 {satnum:05d}U "
        f"{epoch_str} "
        f".00000000 "      # Mean motion dot
        f"00000-0 "        # Mean motion ddot
        f"00000+0 "        # B*
        f"0  999"
    )
    line1 = line1_body.ljust(68) + tle_checksum(line1_body)

    # 第2行
    line2_body = (
        f"2 {satnum:05d} "
        f"{inclination} "
        f"{raan_str} "
        f"{eccentricity} "
        f"{arg_perigee} "
        f"{mean_anom} "
        f"{mean_mot} "
        f"{rev_number:5s}"
    )
    line2 = line2_body.ljust(68) + tle_checksum(line2_body)

    return SatelliteModel(
        id=id,
        order=order,
        plane=plane,
        altitude=altitude,
        tle1text=line1,
        tle2text=line2
    )

# def generate_satellites_with_tle(n_sats, tle_line1, tle_line2, fov_l=30, fov_w=30, altitude=500e3):
#     sats = []
#     for i in range(n_sats):
#         mean_anomaly = (360.0 / n_sats) * i
#         ma_str = f"{mean_anomaly:8.4f}"
#         new_line2 = tle_line2[:43] + ma_str + tle_line2[51:]
#         sat = Satellite(tle_line1, new_line2, f"{i+1:02d}", TS, fov_l=fov_l, fov_w=fov_w, altitude=altitude)
#         sats.append(sat)
#     return sats

def tle_checksum(line: str) -> str:
    total = 0
    for c in line[:68]:
        if c.isdigit():
            total += int(c)
        elif c == '-':
            total += 1
    return str(total % 10)
