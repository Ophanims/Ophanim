"""One-way v0 Ophanim boundary -> canonical application contract; no aliases leak inward."""
from datetime import datetime, timedelta, timezone
from simulator.schemas.project import Project


def import_ophanim_project(legacy_project_id: int, legacy: dict, legacy_stations: list[dict]) -> Project:
    project_id = str(legacy_project_id)
    start_time = legacy.get("startTime") or datetime.now(timezone.utc)
    if isinstance(start_time, str):
        start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    end_time = legacy.get("endTime") or start_time + timedelta(hours=2)
    if isinstance(end_time, datetime):
        end_time = end_time.isoformat()
    number_of_planes = int(legacy.get("maximumNumberOfPlane") or 1)
    satellite_count = int(legacy.get("sizeOfConstellation") or 1)
    if satellite_count % number_of_planes:
        raise ValueError("Constellation size must be divisible by the number of planes")
    hardware = {"id": f"{project_id}_hardware", "project_id": project_id,
                "width_px": legacy.get("imageryWidthPx") or 1920,
                "length_px": legacy.get("imageryHeightPx") or 1080,
                "focal_length_mm": legacy.get("lengthOfCameraFocalMm") or 50,
                "px_size_width": legacy.get("lengthOfCameraSensorUnitUm") or 5.5,
                "px_size_length": legacy.get("lengthOfCameraSensorUnitUm") or 5.5,
                "channels_per_pixel": legacy.get("channelsPerPixel") or 3,
                "bits_per_channel": legacy.get("bitsPerChannelBit") or 8}
    for direction, old_direction, bandwidth_direction in [("downlink", "Dl", "Dl"), ("uplink", "Up", "Ul"), ("isl", "Isl", "Isl")]:
        hardware[f"{direction}_frequency_hz"] = (legacy.get(f"carrierFrequencyOf{old_direction}Ghz") or 2) * 1e9
        hardware[f"{direction}_bandwidth_hz"] = (legacy.get(f"bandwidthOf{bandwidth_direction}Mhz") or 20) * 1e6
        hardware[f"{direction}_tx_power_w"] = 10
        hardware[f"{direction}_gain_tx_dbi"] = legacy.get(f"antennaGainOf{bandwidth_direction}TransmitDbi") or 30
        hardware[f"{direction}_gain_rx_dbi"] = legacy.get(f"antennaGainOf{bandwidth_direction}ReceiveDbi") or 30
        hardware[f"{direction}_noise_temp_k"] = 300
    resources = {}
    if legacy.get("maximumNumberOfProcessorCore") is not None:
        resources["processor_core_count"] = legacy["maximumNumberOfProcessorCore"]
    if legacy.get("factorOfComputationEnergy") is not None:
        resources["computation_energy_factor"] = legacy["factorOfComputationEnergy"]
    if legacy.get("maximumConcurrentComputation") is not None:
        resources["max_concurrent_computations"] = legacy["maximumConcurrentComputation"]
    if legacy.get("maximumClockFrequencyGhz") is not None:
        resources["max_clock_frequency_ghz"] = legacy["maximumClockFrequencyGhz"]
    if legacy.get("factorOfTransmissionEnergy") is not None:
        resources["transmission_energy_factor"] = legacy["factorOfTransmissionEnergy"]
    if legacy.get("efficiencyOfTargetSpectrum") is not None:
        resources["spectral_efficiency"] = legacy["efficiencyOfTargetSpectrum"]
    if legacy.get("maximumConcurrentTransmission") is not None:
        resources["max_concurrent_transmissions"] = legacy["maximumConcurrentTransmission"]
    if legacy.get("batteryCapacityWh") is not None:
        resources["battery_capacity_wh"] = legacy["batteryCapacityWh"]
    if legacy.get("areaOfSolarPanelM2") is not None:
        resources["solar_panel_area_m2"] = legacy["areaOfSolarPanelM2"]
    if legacy.get("efficiencyOfSolarPanel") is not None:
        resources["solar_panel_efficiency"] = legacy["efficiencyOfSolarPanel"]
    if legacy.get("efficiencyOfPowerAmplifier") is not None:
        resources["amplifier_efficiency"] = legacy["efficiencyOfPowerAmplifier"]
    if legacy.get("staticPowerOfProcessingW") is not None:
        resources["static_processing_power_w"] = legacy["staticPowerOfProcessingW"]
    if legacy.get("staticPowerOfIslTransmittingW") is not None:
        resources["static_isl_power_w"] = legacy["staticPowerOfIslTransmittingW"]
    if legacy.get("staticPowerOfUplinkTransmittingW") is not None:
        resources["static_uplink_power_w"] = legacy["staticPowerOfUplinkTransmittingW"]
    if legacy.get("staticPowerOfDownlinkTransmittingW") is not None:
        resources["static_downlink_power_w"] = legacy["staticPowerOfDownlinkTransmittingW"]
    if legacy.get("staticPowerOfOthersW") is not None:
        resources["static_other_power_w"] = legacy["staticPowerOfOthersW"]
    return Project.model_validate({
        "project_id": project_id, "seed": legacy.get("seed") or 0, "algorithm": "ophanim", "user_id": "local", "title": legacy.get("name") or "Imported Ophanim project",
        "description": legacy.get("description") or "", "hardware": hardware, "resources": resources,
        "constellation": {"id": f"{project_id}_constellation", "project_id": project_id,
                          "name": legacy.get("name") or project_id, "number_of_planes": number_of_planes,
                          "number_of_sat_per_planes": satellite_count // number_of_planes,
                          "phase_factor": legacy.get("phaseFactor") or 0, "altitude": legacy.get("altitude") or 600000,
                          "inclination": legacy.get("inclination") if legacy.get("inclination") is not None else 90},
        "experiment": {"id": f"{project_id}_experiment", "project_id": project_id,
                       "start_time": start_time.isoformat(), "end_time": end_time,
                       "time_slot": legacy.get("timeSlot") or 30, "missions": []},
        "satellites": [], "rois": [],
        "ground_stations": [{"id": str(station["id"]) if str(station["id"]).startswith("station_") else f"station_{station['id']}", "project_id": project_id,
                             "name": station["name"], "altitude_m": station.get("altitude", 0), "location": {"lat": station["latitude"], "lon": station["longitude"]}}
                            for station in legacy_stations],
    })
