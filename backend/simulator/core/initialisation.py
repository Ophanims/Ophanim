"""Shared construction for visualization, baselines and reinforcement learning."""
from datetime import datetime, timedelta, timezone
from collections.abc import Sequence
from simulator.entities.functions.prepare import (
    preparation_of_earth, preparation_of_roi, preparation_of_satellite,
    preparation_of_station, preparation_of_sun,
)
from simulator.core.timeline import SimulationTimeline
from simulator.models.realtime_ephemeris import EphemerisSamples
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
    datetime_list = SimulationTimeline(t_start, t_end, period)
    max_period_numbers = len(datetime_list)
    return {"t_start": t_start, "t_end": t_end, "time_recorder": t_start,
            "period": period, "max_period_numbers": max_period_numbers,
            "datetime_list": datetime_list}


def build_static_objects(input: Project, period: timedelta, max_period_numbers: int, datetime_list: Sequence[datetime]):
    # Preserve the construction interface used by all algorithms; evaluate
    # samples only when requested, sharing bounded ephemeris data per session.
    times = EphemerisSamples(datetime_list)
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
