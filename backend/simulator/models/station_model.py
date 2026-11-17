from skyfield.api import wgs84

from simulator.schemas.base import XYZ, LatLon

class StationModel:
    def __init__(self,
        lat: float,
        lon: float,
        id: str = "None",
    ):
        self.id = id
        self.loc = LatLon(lat=lat, lon=lon)
        self.pos = XYZ(x=0.0, y=0.0, z=0.0 )

    def locate(self, t) -> None:
        self.topo = wgs84.latlon(self.loc.lat, self.loc.lon)
        position = self.topo.at(t).position.m
        self.pos = XYZ(x=position[0], y=position[1], z=position[2])
