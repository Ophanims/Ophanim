"""Running observation/return statistics, independent of environment wrappers."""
import json
from pathlib import Path
import numpy as np


class RunningMoments:
    def __init__(self, shape=()):
        self.mean = np.zeros(shape, dtype=np.float64)
        self.var = np.ones(shape, dtype=np.float64)
        self.count = 1e-4

    def update(self, batch):
        batch = np.asarray(batch, dtype=np.float64)
        count, mean, variance = len(batch), batch.mean(axis=0), batch.var(axis=0)
        total = self.count + count
        delta = mean - self.mean
        combined = self.var * self.count + variance * count + delta**2 * self.count * count / total
        self.mean = self.mean + delta * count / total
        self.var, self.count = combined / total, total

    def serialize(self):
        return {"mean": self.mean.tolist(), "var": self.var.tolist(), "count": float(self.count)}

    @classmethod
    def restore(cls, state):
        result = cls()
        result.mean, result.var = np.asarray(state["mean"], dtype=np.float64), np.asarray(state["var"], dtype=np.float64)
        result.count = float(state["count"])
        if result.mean.shape != result.var.shape or result.count <= 0 or (result.var < 0).any():
            raise ValueError("Invalid running statistics")
        if not np.isfinite(result.mean).all() or not np.isfinite(result.var).all():
            raise ValueError("Nonfinite running statistics")
        return result


class Normalizer:
    def __init__(self, shapes, gamma=0.99):
        self.obs_rms = {key: RunningMoments(shape) for key, shape in shapes.items()}
        self.ret_rms = RunningMoments()
        self.gamma, self.epsilon = gamma, 1e-8
        self.clip_obs = self.clip_reward = 10.0
        self.norm_obs = self.norm_reward = True
        self.discounted_returns = {}

    def normalize_obs(self, observation):
        return {key: np.clip((value - self.obs_rms[key].mean) /
                 np.sqrt(self.obs_rms[key].var + self.epsilon), -self.clip_obs, self.clip_obs).astype(np.float32)
                if self.norm_obs and key in self.obs_rms else value.copy() for key, value in observation.items()}

    def observe(self, observation):
        for key, moments in self.obs_rms.items():
            moments.update(np.expand_dims(observation[key], axis=0))
        return self.normalize_obs(observation)

    def reward(self, value, stream_id, completed):
        discounted = self.gamma * self.discounted_returns.get(stream_id, 0.0) + value
        self.ret_rms.update(np.asarray([discounted]))
        self.discounted_returns[stream_id] = 0.0 if completed else discounted
        if not self.norm_reward:
            return float(value)
        return float(np.clip(value / np.sqrt(self.ret_rms.var + self.epsilon), -self.clip_reward, self.clip_reward))

    def save(self, path):
        state = {"schema_version": 1, "observations": {key: value.serialize() for key, value in self.obs_rms.items()},
                 "returns": self.ret_rms.serialize(), "gamma": self.gamma, "epsilon": self.epsilon,
                 "clip_obs": self.clip_obs, "clip_reward": self.clip_reward, "norm_obs": self.norm_obs}
        Path(path).write_text(json.dumps(state, allow_nan=False))

    @classmethod
    def load(cls, path):
        state = json.loads(Path(path).read_text())
        if state["schema_version"] != 1:
            raise ValueError("Unsupported normalizer version")
        result = cls({})
        result.obs_rms = {key: RunningMoments.restore(value) for key, value in state["observations"].items()}
        result.ret_rms = RunningMoments.restore(state["returns"])
        for key in ("gamma", "epsilon", "clip_obs", "clip_reward", "norm_obs"):
            setattr(result, key, state[key])
        return result
