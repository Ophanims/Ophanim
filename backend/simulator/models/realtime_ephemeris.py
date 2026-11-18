"""Evaluate the existing geometric formulas at the requested simulation time."""
import numpy as np
from pyproj import Geod
from skyfield.api import load, wgs84

from simulator.config import EPHEMERIS
from simulator.models.sampled_data import SampleCache

TS = load.timescale()
GEOD = Geod(ellps="WGS84")
EARTH = EPHEMERIS["earth"]
SUN = EPHEMERIS["sun"]


class EphemerisSamples:
    def __init__(self, timeline):
        self.timeline = timeline
        self.times = SampleCache()
        self.sun = SampleCache()

    def time_at(self, index):
        return self.times.get(index, lambda position: TS.utc(self.timeline[position]))

    def sun_at(self, index):
        return self.sun.get(index, lambda position: EARTH.at(self.time_at(position)).observe(SUN).apparent().position.m)


class SatelliteSamples:
    def __init__(self, satellite, ephemeris: EphemerisSamples):
        self.satellite = satellite
        self.ephemeris = ephemeris
        self.timeline = ephemeris.timeline
        self.states = SampleCache(2)
        self.positions = SampleCache(4)
        self.sunlight = SampleCache(2048)

    def position_at(self, index):
        return self.positions.get(index, lambda position: self.satellite.motion.at(self.ephemeris.time_at(position)))

    def sunlit_at(self, index):
        return self.sunlight.get(index, lambda position: bool(self.position_at(position).is_sunlit(EPHEMERIS)))

    def sunlit_many(self, indices):
        # Algorithms may ask for future sunlight. Compute only that window, with
        # a bounded cache, without building positions/footprints for future frames.
        indices = list(indices)
        missing = [index for index in indices if index not in self.sunlight.samples]
        calculated = {}
        if missing:
            times = TS.utc([self.timeline[index] for index in missing])
            values = self.satellite.motion.at(times).is_sunlit(EPHEMERIS)
            calculated = dict(zip(missing, map(bool, values)))
        requested = {index: self.sunlight.samples[index] if index in self.sunlight.samples else calculated[index]
                     for index in indices}
        for index in indices:
            self.sunlight.get(index, lambda position: requested[position])
        return np.asarray([requested[index] for index in indices], dtype=bool)

    def at(self, index):
        return self.states.get(index, self._calculate)

    def _calculate(self, index):
        satellite = self.satellite
        time = self.ephemeris.time_at(index)
        geos = self.position_at(index)
        pos = geos.position.m
        subpoint = geos.subpoint()
        lat, lon = subpoint.latitude.degrees, subpoint.longitude.degrees
        # Preserve the previous implementation's forward difference and its
        # backward difference at the clipped final sample (including azimuth).
        neighbor_index = index + 1 if index + 1 < len(self.timeline) else index - 1
        neighbor = self.position_at(neighbor_index)
        neighbor_subpoint = neighbor.subpoint()
        if neighbor_index > index:
            velocity = neighbor.position.m - pos
            azimuth = GEOD.inv(lon, lat, neighbor_subpoint.longitude.degrees, neighbor_subpoint.latitude.degrees)[0] % 360
        else:
            velocity = pos - neighbor.position.m
            azimuth = GEOD.inv(neighbor_subpoint.longitude.degrees, neighbor_subpoint.latitude.degrees, lon, lat)[0] % 360
        corners_latlon = np.asarray(satellite.camera.coverage_corners(satellite.altitude, lon, lat, azimuth))
        corners_xyz = np.asarray([wgs84.latlon(corner_lat, corner_lon).at(time).position.m
                                  for corner_lat, corner_lon in corners_latlon])
        solar = self.ephemeris.sun_at(index) - pos
        return {
            "space_xyz": pos,
            "subpoint_xyz": wgs84.latlon(lat, lon).at(time).position.m,
            "subpoint_latlon": np.asarray([lat, lon]),
            "azimuth": azimuth,
            "footprint_corners_latlon": corners_latlon,
            "footprint_corners_xyz": corners_xyz,
            "solar_vector": solar / np.linalg.norm(solar),
            "velocity_vector": velocity / np.linalg.norm(velocity),
        }


class GroundSamples:
    def __init__(self, lat, lon, ephemeris: EphemerisSamples, corners_latlon=None):
        self.ephemeris = ephemeris
        self.topos = wgs84.latlon(lat, lon)
        self.corners = [] if corners_latlon is None else [wgs84.latlon(*corner) for corner in corners_latlon]
        self.states = SampleCache(2)

    def at(self, index):
        return self.states.get(index, self._calculate)

    def _calculate(self, index):
        time = self.ephemeris.time_at(index)
        return {"xyz": self.topos.at(time).position.m,
                "corners_xyz": np.asarray([corner.at(time).position.m for corner in self.corners])}
