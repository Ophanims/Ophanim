import os
from skyfield.api import load
import numpy as np
from pyproj import Geod

BSP_FILE = os.path.join('de421.bsp')
BASE_AZI = np.array([45, 135, 225, 315])
TS = load.timescale()
EPHEMERIS = load(BSP_FILE)
GEOD = Geod(ellps="WGS84")
SUN = EPHEMERIS['sun']
EARTH = EPHEMERIS['earth']
MOON = EPHEMERIS['moon']

DEFAULT_SIMULATION_TIMESLOT = 30.0  # seconds
DEFAULT_ALTITUDE = 550.0  # km
DEFAULT_INCLINATION = 55.0  # degrees
DEFAULT_CONSTELLATION_SIZE = 1  # satellites
DEFAULT_PLANE_COUNT = 1  # planes
DEFAULT_PHASE_FACTOR = 0.0  # radians

R_EARTH = 6371000.0
MU = 3.986004418e14  # 地球引力常数，单位：m^3/s^2