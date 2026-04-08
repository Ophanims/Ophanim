from typing import List
import numpy as np
from skyfield.api import EarthSatellite, Time, wgs84, load


class Network:
    def __init__(
        self,
        satellites: list,
        ground_stations: list,
    ):
        self.satellites = satellites
        self.ground_stations = ground_stations
        self.links: list = []  # 存储所有链路对象
        
    