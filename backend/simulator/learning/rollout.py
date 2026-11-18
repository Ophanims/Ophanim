"""Training samples come directly from complete Simulation transitions."""
from dataclasses import dataclass
import numpy as np
import torch
from simulator.core.simulation import Simulation
from simulator.core.time_step import step_context
from simulator.policies.discrete_scheduler import DiscreteScheduler
from simulator.policies.reward import transition_reward
from simulator.policies.view import PlanningView


@dataclass
class Transition:
    features: np.ndarray
    action: int
    mask: np.ndarray
    value: float
    log_prob: float
    reward: float
    completed: bool = False


@dataclass
class Rollout:
    features: np.ndarray
    actions: np.ndarray
    masks: np.ndarray
    values: np.ndarray
    log_probs: np.ndarray
    advantages: np.ndarray
    returns: np.ndarray
    rewards: np.ndarray

    def __len__(self):
        return len(self.actions)


def compute_gae(rewards, values, completed, bootstrap, gamma=0.99, gae_lambda=0.95):
    advantages = np.empty(len(rewards), dtype=np.float32)
    next_value, accumulated = bootstrap, 0.0
    for index in reversed(range(len(rewards))):
        continuation = 0.0 if completed[index] else 1.0
        delta = rewards[index] + gamma * next_value * continuation - values[index]
        accumulated = delta + gamma * gae_lambda * continuation * accumulated
        advantages[index] = accumulated
        next_value = values[index]
    return advantages, advantages + np.asarray(values, dtype=np.float32)


class RolloutCollector:
    def __init__(self, project, seeds, lamda=0.57):
        self.seeds = tuple(seeds)
        if not self.seeds:
            raise ValueError("Training needs at least one seed")
        self.simulators = []
        self.generators = [torch.Generator().manual_seed(seed) for seed in self.seeds]
        self.lamda, self.stream_index = lamda, 0
        self.episode_rewards = [0.0] * len(self.seeds)
        self.episode_lengths = [0] * len(self.seeds)
        self.episodes = []
        try:
            for seed in self.seeds:
                simulator = Simulation(project)
                self.simulators.append(simulator)
                simulator.reset(seed=seed)
        except Exception:
            self.close()
            raise

    @staticmethod
    def observe(simulator):
        scheduler = DiscreteScheduler()
        scheduler.begin(PlanningView.from_simulator(simulator))
        return scheduler.observation()

    def _sample_slot(self, index, model, normalizer):
        simulator = self.simulators[index]
        before, context = simulator.snapshot(), step_context(simulator)
        scheduler = DiscreteScheduler()
        scheduler.begin(PlanningView.from_simulator(simulator))
        samples = []
        # Do not update weights in the middle of a physical slot. All actions
        # see the same s_t; their only side effects are local reservations.
        while not samples or not scheduler.finished:
            observation = normalizer.observe(scheduler.observation())
            mask = scheduler.action_masks().astype(bool)
            decision = model.choose_action(observation, mask, deterministic=False, generator=self.generators[index])
            reward = scheduler.submit(decision.action)
            samples.append(Transition(model.vectorize(observation), decision.action, mask,
                                      decision.value, decision.log_prob, reward))
        actions = scheduler.actions()
        simulator.step(actions)
        samples[-1].reward = transition_reward(before, simulator, actions, context, samples[-1].reward, self.lamda)
        samples[-1].completed = simulator.is_completed
        for sample in samples:
            self.episode_rewards[index] += sample.reward
            self.episode_lengths[index] += 1
            sample.reward = normalizer.reward(sample.reward, index, sample.completed)
        if simulator.info.terminated_reason == "end_time_reached":
            observation = normalizer.normalize_obs(self.observe(simulator))
            samples[-1].reward += normalizer.gamma * model.value(observation)
        if simulator.is_completed:
            self.episodes.append({"reward": self.episode_rewards[index], "length": self.episode_lengths[index],
                                  "seed": self.seeds[index]})
            self.episode_rewards[index] = self.episode_lengths[index] = 0
            simulator.reset(seed=self.seeds[index])
        return samples

    def collect(self, model, normalizer, min_samples, gae_lambda=0.95):
        if min_samples < 1:
            raise ValueError("Rollout size must be positive")
        streams = [[] for _ in self.simulators]
        count = 0
        while count < min_samples:
            index = self.stream_index
            samples = self._sample_slot(index, model, normalizer)
            streams[index].extend(samples)
            count += len(samples)
            self.stream_index = (index + 1) % len(self.simulators)
        all_samples, all_advantages, all_returns = [], [], []
        for index, samples in enumerate(streams):
            if not samples:
                continue
            bootstrap = 0.0 if samples[-1].completed else model.value(
                normalizer.normalize_obs(self.observe(self.simulators[index])))
            advantages, returns = compute_gae([sample.reward for sample in samples],
                [sample.value for sample in samples], [sample.completed for sample in samples],
                bootstrap, normalizer.gamma, gae_lambda)
            all_samples.extend(samples)
            all_advantages.extend(advantages)
            all_returns.extend(returns)
        return Rollout(np.stack([s.features for s in all_samples]), np.asarray([s.action for s in all_samples]),
            np.stack([s.mask for s in all_samples]), np.asarray([s.value for s in all_samples], np.float32),
            np.asarray([s.log_prob for s in all_samples], np.float32), np.asarray(all_advantages, np.float32),
            np.asarray(all_returns, np.float32), np.asarray([s.reward for s in all_samples], np.float32))

    def close(self):
        for simulator in self.simulators:
            simulator.close()
