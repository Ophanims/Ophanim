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