"""Gym input/output adapter around Simulation; contains no environment dynamics."""
import gymnasium as gym
from gymnasium import spaces
from simulator.core.simulation import Simulation
from simulator.core.time_step import step_context
from simulator.env.core.observation import get_obs_space_shape
from simulator.policies.discrete_scheduler import DiscreteScheduler
from simulator.policies.reward import transition_reward
from simulator.policies.view import PlanningView


class SimulationGymAdapter(gym.Env):
    metadata = {"render_modes": ["human"]}

    def __init__(self, project):
        super().__init__()
        self.simulator = Simulation(project)
        self.action_space = spaces.Discrete(6)
        self.observation_space = get_obs_space_shape(project.constellation.number_of_sat_per_planes,
                                                     project.constellation.number_of_planes)
        self.lamda = 0.57
        self._begin_slot()

    def _begin_slot(self):
        self.scheduler = DiscreteScheduler()
        self.scheduler.begin(PlanningView.from_simulator(self.simulator))

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.simulator.reset(seed=seed)
        self._begin_slot()
        return self.scheduler.observation(), {}

    def action_masks(self):
        return self.scheduler.action_masks()

    def step(self, action):
        if self.simulator.is_completed:
            return self.scheduler.observation(), 0.0, True, False, self.simulator.info.serialize()
        reward = self.scheduler.submit(action)
        if not self.scheduler.finished:
            return self.scheduler.observation(), reward, False, False, {"reward": reward}
        before = self.simulator.snapshot()
        context = step_context(self.simulator)
        actions = self.scheduler.actions()
        self.simulator.step(actions)
        reward = transition_reward(before, self.simulator, actions, context, reward, self.lamda)
        truncated = self.simulator.info.terminated_reason == "end_time_reached"
        terminated = self.simulator.is_completed and not truncated
        info = self.simulator.info.model_copy(update={"reward": reward, "is_terminated": terminated,
            "is_truncated": truncated, "truncated_reason": "end_time_reached" if truncated else "None"}).serialize()
        self._begin_slot()
        return self.scheduler.observation(), reward, terminated, truncated, info

    def close(self):
        self.simulator.close()
