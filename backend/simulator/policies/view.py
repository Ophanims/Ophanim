"""Detached policy inputs; this object cannot step, reset or publish a world."""
import math
from dataclasses import dataclass
from simulator.core.staging import fork_environment
from simulator.contracts import SimulationSnapshot


@dataclass
class PlanningView:
    state: SimulationSnapshot
    sat: list
    gs: list
    net: object
    task_manager: object
    entity_collection: object
    comp_reqs: list
    trans_reqs: list
    task_isl_hops: dict
    frame_counter: int
    period_counter: int
    slot_counter: int
    slot_in_num: float
    period_in_num: float
    orbital_period: int
    logger: object
    input: object

    @classmethod
    def from_simulator(cls, simulator):
        candidate = fork_environment(simulator)
        for node in candidate.sat:
            node.clear_indicators()
        return cls(simulator.snapshot(), candidate.sat, candidate.gs, candidate.net,
            candidate.task_manager, candidate.entity_collection, candidate.comp_reqs,
            candidate.trans_reqs, candidate.task_isl_hops, candidate.frame_counter,
            candidate.period_counter, candidate.slot_counter, candidate.slot_in_num,
            candidate.period_in_num, math.ceil(candidate.input.constellation.orbital_period /
                                               candidate.period_in_num), candidate.logger, candidate.input.snapshot())
