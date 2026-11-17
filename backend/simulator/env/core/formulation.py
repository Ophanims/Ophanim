from typing import List

import numpy as np
from simulator.schemas.task import Task
from simulator.entities.satellite_entity import SatelliteEntity
from simulator.config import BATTERY_MAX, COMPUTE_ENERGY_COST, LAYER_PROCESS_SECOND_COST_GPU, STATIC_ENERGY_COST, TRANSMIT_ISL_ENERGY_COST, TRANSMIT_SGL_ENERGY_COST


def compute_delay_penalty(slot: float, tasks: List[Task]):

    _len = len(LAYER_PROCESS_SECOND_COST_GPU)
    _all_workload = sum(LAYER_PROCESS_SECOND_COST_GPU) / slot
    delays = []
    for t in tasks:
        _workload_left = sum(LAYER_PROCESS_SECOND_COST_GPU[i] / slot for i in range(t.layer_id, _len))
        delays.append(_workload_left/ _all_workload)

        # duration = t.t_end - t.t_start
        # max_allowed = t.ddl - t.t_start
        # _delay_ratio = duration / max_allowed
        # _delay_ratio = min(max(_delay_ratio, 0.0), 1.0)

        # delays.append(_delay_ratio)

    # return max(delays)
    return np.mean(delays)


# def compute_energy_penalty(nodes: List[SatelliteEntity]):
#     if not nodes:
#         return 0.0

#     costs = []
#     for n in nodes:
#         _cost = (1.0 - n.battery_ratio)
#         costs.append(_cost)

#     # return max(costs)
#     return np.mean(costs)

def compute_energy_penalty(slot: float, nodes: List[SatelliteEntity]):
    if not nodes:
        return 0.0

    max_power_w = abs(
        # TRANSMIT_SGL_ENERGY_COST +
        TRANSMIT_ISL_ENERGY_COST +
        COMPUTE_ENERGY_COST +
        STATIC_ENERGY_COST
    )

    max_step_joules = slot * max_power_w

    costs = []
    for n in nodes:
        consumed_joules = abs(n.cost_percent / 100.0) * BATTERY_MAX
        # print(f"Satellite {n.id} consumed_joules: {consumed_joules:.2f}J")
        _cost = consumed_joules / (max_step_joules + 1e-9)
        costs.append(_cost)

    avg = np.mean(costs)
    # print(f"max_step_joules: {max_step_joules:.2f}, avg energy cost ratio: {avg:.4f}")
    return avg

def reward_function(lamda: float, delay_penalty: float, energy_penalty: float, scale: float = 1.0) -> float:
    """
    Lexicographic objective: prioritize one objective first, break ties with the other.

    - If primary == 'delay': minimize delay first (maximize 1-delay), then among equal delay
      prefer lower energy. Implemented as a large weight on the primary objective plus
      a small secondary bonus.
    - Reverse if primary == 'energy'.
    """
    latency = max(delay_penalty, 0.0)
    energy_cost = max(energy_penalty, 0.0)

    base_reward = (lamda * energy_cost + (1 - lamda) * latency)
    R = -1.0 * base_reward * scale

    return R
