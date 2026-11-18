"""Construct entities with on-demand geometry; no trajectory files or preloading."""
import numpy as np

from simulator.entities.earth_entity import EarthEntity
from simulator.entities.roi_entity import ROIEntity
from simulator.entities.satellite_entity import SatelliteEntity
from simulator.entities.station_entity import StationEntity
from simulator.entities.sun_entity import SunEntity
from simulator.models.camera_model import CameraModel
from simulator.models.realtime_ephemeris import EphemerisSamples, GroundSamples, SatelliteSamples, GEOD
from simulator.models.roi_model import ROIModel
from simulator.models.sampled_data import SampleSeries, sample_columns
from simulator.models.satellite_model import SatelliteModel
from simulator.models.station_model import StationModel
from simulator.schemas.project import Project


def preparation_of_satellite(input: Project, steps, times, datetimes):
    ephemeris = times if isinstance(times, EphemerisSamples) else EphemerisSamples(datetimes)
    sat_datas = []
    for satellite in get_sat_from_project(input):
        samples = SatelliteSamples(satellite, ephemeris)
        data = sample_columns(datetimes, samples, (
            "space_xyz", "subpoint_xyz", "subpoint_latlon", "azimuth",
            "footprint_corners_latlon", "footprint_corners_xyz", "solar_vector", "velocity_vector",
        ))
        data.update(id=satellite.id, order=satellite.order, plane=satellite.plane,
                    altitude=satellite.altitude, time=datetimes,
                    is_sunlit=SampleSeries(datetimes, samples.sunlit_at, samples.sunlit_many),
                    swath_length=satellite.camera.calc_swath_length(satellite.altitude),
                    swath_width=satellite.camera.calc_swath_width(satellite.altitude))
        sat_datas.append(data)
    return [SatelliteEntity(time_series=data) for data in sat_datas], sat_datas


def preparation_of_station(input: Project, times, datetimes):
    ephemeris = times if isinstance(times, EphemerisSamples) else EphemerisSamples(datetimes)
    gs_datas = []
    for station in get_gs_from_project(input):
        samples = GroundSamples(station.loc.lat, station.loc.lon, ephemeris)
        data = sample_columns(datetimes, samples, ("xyz",))
        data.update(id=station.id, time=datetimes, latlon=np.asarray([station.loc.lat, station.loc.lon]))
        gs_datas.append(data)
    return [StationEntity(time_series=data) for data in gs_datas], gs_datas


def preparation_of_roi(input: Project, steps, times, datetimes):
    ephemeris = times if isinstance(times, EphemerisSamples) else EphemerisSamples(datetimes)
    roi_datas = []
    for roi in get_roi_from_project(input):
        offsets = [(roi.length / 2, roi.width / 2), (roi.length / 2, -roi.width / 2),
                   (-roi.length / 2, -roi.width / 2), (-roi.length / 2, roi.width / 2)]
        azimuths = [np.degrees(np.arctan2(dx, dy)) % 360 for dy, dx in offsets]
        distances = [np.hypot(dx, dy) for dy, dx in offsets]
        lons, lats, _ = GEOD.fwd(np.full(4, roi.loc.lon), np.full(4, roi.loc.lat), azimuths, distances)
        corners = np.column_stack((lats, ((lons + 180) % 360) - 180))
        samples = GroundSamples(roi.loc.lat, roi.loc.lon, ephemeris, corners)
        data = {"id": roi.id, "time": datetimes, "roi_length": roi.length, "roi_width": roi.width,
                "center_latlon": np.asarray([roi.loc.lat, roi.loc.lon]), "target_corners_latlon": corners,
                "center_xyz": SampleSeries(datetimes, lambda index, samples=samples: samples.at(index)["xyz"]),
                "target_corners_xyz": SampleSeries(datetimes, lambda index, samples=samples: samples.at(index)["corners_xyz"])}
        roi_datas.append(data)
    return [ROIEntity(time_series=data) for data in roi_datas], roi_datas


def preparation_of_sun(times, datetimes):
    ephemeris = times if isinstance(times, EphemerisSamples) else EphemerisSamples(datetimes)
    data = {"id": "sun", "time": datetimes, "xyz": SampleSeries(datetimes, ephemeris.sun_at)}
    return SunEntity(time_series=data), data


def preparation_of_earth(dt, times, datetimes):
    data = {"id": "earth", "time": datetimes,
            "xyz": SampleSeries(datetimes, lambda index: np.zeros(3)),
            "rotation": SampleSeries(datetimes, lambda index: 2 * np.pi / 86400 * (datetimes[index] - datetimes[0]).total_seconds())}
    return EarthEntity(time_series=data), data


def get_sat_from_project(input: Project) -> list[SatelliteModel]:
    camera = CameraModel.from_dict(input.hardware)
    satellites = [SatelliteModel(altitude=input.constellation.altitude, id=satellite.id,
                                order=satellite.order, plane=satellite.plane,
                                tle1text=satellite.tle1, tle2text=satellite.tle2)
                  for satellite in input.satellites or []]
    for satellite in satellites:
        satellite.camera = camera
    return satellites


def get_gs_from_project(input: Project) -> list[StationModel]:
    return [StationModel(lat=station.location.lat, lon=station.location.lon, id=station.id)
            for station in input.ground_stations or []]


def get_roi_from_project(input: Project) -> list[ROIModel]:
    return [ROIModel(lat=roi.location.lat, lon=roi.location.lon, id=roi.id, length=roi.length, width=roi.width)
            for roi in input.rois or []]
