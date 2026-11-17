from pydantic import Field
from simulator.schemas.base import ContractModel


class Resources(ContractModel):
    processor_core_count: int = Field(4, ge=0)
    computation_energy_factor: float = Field(1e-27, ge=0)
    max_concurrent_computations: int = Field(4, ge=0)
    max_clock_frequency_ghz: float = Field(1, ge=0)
    transmission_energy_factor: float = Field(1, ge=0)
    spectral_efficiency: float = Field(1, ge=0)
    max_concurrent_transmissions: int = Field(4, ge=0)
    battery_capacity_wh: float = Field(60, gt=0)
    solar_panel_area_m2: float = Field(0.3, gt=0)
    solar_panel_efficiency: float = Field(0.3, ge=0, le=1)
    amplifier_efficiency: float = Field(0.8, gt=0, le=1)
    static_processing_power_w: float = Field(10, ge=0)
    static_isl_power_w: float = Field(5, ge=0)
    static_uplink_power_w: float = Field(5, ge=0)
    static_downlink_power_w: float = Field(5, ge=0)
    static_other_power_w: float = Field(10, ge=0)
