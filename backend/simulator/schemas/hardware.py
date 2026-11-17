from pydantic import Field
from simulator.schemas.base import ContractModel


class Hardware(ContractModel):
    id: str
    project_id: str
    focal_length_mm: float = Field(50.0, gt=0)
    width_px: int = Field(1920, gt=0)
    length_px: int = Field(1080, gt=0)
    px_size_width: float = Field(5.5, gt=0)
    px_size_length: float = Field(5.5, gt=0)
    channels_per_pixel: int = Field(3, gt=0)
    bits_per_channel: int = Field(8, gt=0)
    downlink_frequency_hz: float = Field(26000000000.0, gt=0)
    downlink_bandwidth_hz: float = Field(500000000.0, gt=0)
    downlink_tx_power_w: float = Field(10.0, gt=0)
    downlink_gain_tx_dbi: float = Field(30.0)
    downlink_gain_rx_dbi: float = Field(40.0)
    downlink_noise_temp_k: float = Field(300.0, gt=0)
    uplink_frequency_hz: float = Field(30000000000.0, gt=0)
    uplink_bandwidth_hz: float = Field(500000000.0, gt=0)
    uplink_gain_tx_dbi: float = Field(40.0)
    uplink_tx_power_w: float = Field(50.0, gt=0)
    uplink_gain_rx_dbi: float = Field(20.0)
    uplink_noise_temp_k: float = Field(500.0, gt=0)
    isl_frequency_hz: float = Field(50000000000.0, gt=0)
    isl_bandwidth_hz: float = Field(2000000000.0, gt=0)
    isl_tx_power_w: float = Field(5.0, gt=0)
    isl_gain_tx_dbi: float = Field(32.0)
    isl_gain_rx_dbi: float = Field(32.0)
    isl_noise_temp_k: float = Field(400.0, gt=0)
