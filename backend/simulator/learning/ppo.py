"""Clipped PPO/GAE optimizer, independent of any environment API."""
from dataclasses import dataclass
import numpy as np
import torch
from torch.nn import functional as F


@dataclass(frozen=True)
class PPOConfig:
    learning_rate: float = 3e-4
    n_steps: int = 2048
    batch_size: int = 1024
    n_epochs: int = 10
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_range: float = 0.25
    target_kl: float = 0.03
    ent_coef: float = 0.01
    vf_coef: float = 0.5
    max_grad_norm: float = 0.5

    def __post_init__(self):
        if min(self.n_steps, self.batch_size, self.n_epochs) < 1 or self.learning_rate <= 0:
            raise ValueError("Training sizes and learning rate must be positive")


def ppo_loss(log_probs, values, entropy, old_log_probs, advantages, returns, config):
    # Sample std (ddof=1) matches the previous optimizer; singleton remainder
    # batches still have a finite, usable advantage.
    if len(advantages) > 1:
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
    ratio = torch.exp(log_probs - old_log_probs)
    policy_loss = -torch.minimum(advantages * ratio,
        advantages * torch.clamp(ratio, 1 - config.clip_range, 1 + config.clip_range)).mean()
    value_loss = F.mse_loss(values, returns)
    entropy_loss = -entropy.mean()
    loss = policy_loss + config.ent_coef * entropy_loss + config.vf_coef * value_loss
    log_ratio = log_probs - old_log_probs
    approximate_kl = ((torch.exp(log_ratio) - 1) - log_ratio).mean()
    return loss, policy_loss, value_loss, entropy.mean(), approximate_kl


class PPOOptimizer:
    def __init__(self, model, config=PPOConfig(), seed=0):
        self.model, self.config = model, config
        self.optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate, eps=1e-5)
        self.rng = np.random.default_rng(seed)

    def update(self, rollout):
        model, config = self.model, self.config
        model.train()
        metrics = []
        for _ in range(config.n_epochs):
            indices = self.rng.permutation(len(rollout))
            for start in range(0, len(indices), config.batch_size):
                batch = indices[start:start + config.batch_size]
                features = torch.from_numpy(rollout.features[batch])
                actions = torch.from_numpy(rollout.actions[batch]).long()
                logs, values, entropy = model.evaluate(features, actions, rollout.masks[batch])
                loss, policy, value, entropy_mean, kl = ppo_loss(logs, values, entropy,
                    torch.from_numpy(rollout.log_probs[batch]), torch.from_numpy(rollout.advantages[batch]),
                    torch.from_numpy(rollout.returns[batch]), config)
                if not torch.isfinite(loss) or not torch.isfinite(kl):
                    raise ValueError("Nonfinite PPO loss")
                metrics.append([float(tensor.detach()) for tensor in (loss, policy, value, entropy_mean, kl)])
                if kl.detach().item() > 1.5 * config.target_kl:
                    return self._summarize(metrics)
                self.optimizer.zero_grad()
                loss.backward()
                norm = torch.nn.utils.clip_grad_norm_(model.parameters(), config.max_grad_norm)
                if not torch.isfinite(norm):
                    raise ValueError("Nonfinite PPO gradient")
                self.optimizer.step()
        return self._summarize(metrics)

    @staticmethod
    def _summarize(metrics):
        return dict(zip(("loss", "policy_loss", "value_loss", "entropy", "approximate_kl"),
                        np.asarray(metrics).mean(axis=0).tolist()))
