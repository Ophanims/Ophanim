"""Typed physical-model inputs derived from the application's single Project."""
from simulator.schemas.resources import Resources
from simulator.schemas.base import ContractModel
from simulator.schemas.project import Project


class EngineStation(ContractModel):
    name: str
    latitude: float
    longitude: float
    altitude: float = 0


class EngineConfig(Resources):
    name: str
    time_slot: float
    start_time: str
    end_time: str | None
    seed: int
    altitude: float
    inclination: float
    number_of_planes: int
    satellite_count: int
    phase_factor: float
    width_px: int
    length_px: int
    focal_length_mm: float
    pixel_size_um: float
    channels_per_pixel: int
    bits_per_channel: int
    isl_frequency_ghz: float
    uplink_frequency_ghz: float
    downlink_frequency_ghz: float
    isl_bandwidth_mhz: float
    uplink_bandwidth_mhz: float
    downlink_bandwidth_mhz: float
    isl_gain_tx_dbi: float
    isl_gain_rx_dbi: float
    uplink_gain_tx_dbi: float
    uplink_gain_rx_dbi: float
    downlink_gain_tx_dbi: float
    downlink_gain_rx_dbi: float

    @classmethod
    def from_project(cls, project: Project):
        hardware = project.hardware
        data = project.resources.serialize()
        data.update(name=project.title, time_slot=project.experiment.time_slot or 30,
                    start_time=project.experiment.start_time, end_time=project.experiment.end_time,
                    seed=project.seed, altitude=project.constellation.altitude,
                    inclination=project.constellation.inclination,
                    number_of_planes=project.constellation.number_of_planes,
                    satellite_count=project.constellation.number_of_planes * project.constellation.number_of_sat_per_planes,
                    phase_factor=project.constellation.phase_factor, width_px=hardware.width_px,
                    length_px=hardware.length_px, focal_length_mm=hardware.focal_length_mm,
                    pixel_size_um=hardware.px_size_width, channels_per_pixel=hardware.channels_per_pixel,
                    bits_per_channel=hardware.bits_per_channel)
        for direction in ("isl", "uplink", "downlink"):
            data[f"{direction}_frequency_ghz"] = getattr(hardware, f"{direction}_frequency_hz") / 1e9
            data[f"{direction}_bandwidth_mhz"] = getattr(hardware, f"{direction}_bandwidth_hz") / 1e6
            for gain in ("gain_tx_dbi", "gain_rx_dbi"):
                data[f"{direction}_{gain}"] = getattr(hardware, f"{direction}_{gain}")
        return cls.model_validate(data)
