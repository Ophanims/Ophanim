"""Simulator-native numeric observations; shapes are ordinary Python tuples."""
import numpy as np
from simulator.env.io.decision_manager import DecisionManager
from simulator.env.io.state_manager import StateManager
from simulator.env.core.graph_encoder import task_set_stats


OBSERVATION_KEYS = ("energy", "sunlight", "comm", "queue", "task_stats")
ACTION_COUNT = 6


def observation_shapes(o: int, p: int) -> dict[str, tuple[int, ...]]:
    return {"energy": (p, o), "sunlight": (p, o), "comm": (p, o, p, o),
            "queue": (p, o), "task_stats": (42,)}


def validate_observation(observation, shapes):
    if observation.keys() != shapes.keys():
        raise ValueError("Observation fields do not match the model")
    for key, shape in shapes.items():
        value = observation[key]
        if value.shape != shape or value.dtype != np.float32 or not np.isfinite(value).all():
            raise ValueError(f"Invalid observation field: {key}; expected finite float32 {shape}")


def get_obs(sm: StateManager, dm: DecisionManager, step: int):
    beta = sm.report(step)
    observation = {key: np.asarray(beta[key], dtype=np.float32)
                   for key in OBSERVATION_KEYS if key != "task_stats"}
    observation["task_stats"] = task_set_stats(sm)
    validate_observation(observation, observation_shapes(o=sm.O_MAX, p=sm.P_MAX))
    return observation, {"alpha": dm.report(step), "beta": beta, "step": step}
