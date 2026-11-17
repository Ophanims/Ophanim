"""Shared construction for visualization, baselines and reinforcement learning."""
import math
from datetime import datetime, timedelta, timezone
from simulator.entities.functions.prepare import (
    preparation_of_earth, preparation_of_roi, preparation_of_satellite,
    preparation_of_station, preparation_of_sun, to_times,
)
from simulator.schemas.project import Project
from simulator.services.network_service import Network


def normalize_time(value) -> datetime:
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def load_input_metadata(input: Project, max_simulation_period):
    t_start = normalize_time(input.experiment.start_time)
    duration = max_simulation_period if isinstance(max_simulation_period, timedelta) else timedelta(seconds=max_simulation_period)
    t_end = normalize_time(input.experiment.end_time) if input.experiment.end_time else t_start + duration
    if t_end <= t_start:
        raise ValueError("end_time must be after start_time")
    period = timedelta(seconds=input.experiment.time_slot or 30)
    if period.total_seconds() <= 0:
        raise ValueError("time_slot must be positive")
    # Include the endpoint and at least two samples for motion/rotation calculations.
    max_period_numbers = max(2, math.ceil((t_end - t_start) / period) + 1)
    if max_period_numbers * max(1, len(input.satellites)) > 500_000:
        raise ValueError("Timeline exceeds 500000 satellite samples; increase time_slot")
    datetime_list = [min(t_start + index * period, t_end) for index in range(max_period_numbers)]
    return {"t_start": t_start, "t_end": t_end, "time_recorder": t_start,
            "period": period, "max_period_numbers": max_period_numbers,
            "datetime_list": datetime_list}


def build_static_objects(input: Project, period: timedelta, max_period_numbers: int, datetime_list: list[datetime]):
    times = to_times(datetime_list)
    sat, sat_datas = preparation_of_satellite(input, max_period_numbers, times, datetime_list)
    gs, gs_datas = preparation_of_station(input, times, datetime_list)
    roi, roi_datas = preparation_of_roi(input, max_period_numbers, times, datetime_list)
    eth, eth_data = preparation_of_earth(period, times, datetime_list)
    sun, sun_data = preparation_of_sun(times, datetime_list)
    return {"sat": sat, "sat_datas": sat_datas, "gs": gs, "gs_datas": gs_datas,
            "roi": roi, "roi_datas": roi_datas, "eth": eth, "eth_data": eth_data,
            "sun": sun, "sun_data": sun_data}


def init_network(input: Project, sat_datas: list[dict], gs_datas: list[dict]) -> Network:
    return Network(input.constellation.number_of_planes, sat_datas, gs_datas, hardware=input.hardware)
