"""Actor/critic network matching the existing PPO checkpoint architecture."""
from dataclasses import dataclass
import numpy as np
import torch
from torch import nn
from torch.distributions import Categorical
from simulator.env.core.observation import ACTION_COUNT, OBSERVATION_KEYS, observation_shapes, validate_observation
from simulator.settings import SIMULATION_TORCH_THREADS

torch.set_num_threads(SIMULATION_TORCH_THREADS)


@dataclass(frozen=True)
class PolicyDecision:
    action: int
    value: float
    log_prob: float


class ActorCritic(nn.Module):
    def __init__(self, planes: int, orders: int, hidden: int = 256, embed_dim: int = 256):
        super().__init__()
        self.planes, self.orders = planes, orders
        self.hidden, self.embed_dim = hidden, embed_dim
        self.observation_shapes = observation_shapes(o=orders, p=planes)
        input_dim = sum(int(np.prod(shape)) for shape in self.observation_shapes.values())
        self.features = nn.Sequential(nn.Linear(input_dim, hidden), nn.ReLU(),
                                      nn.Linear(hidden, embed_dim), nn.ReLU())
        self.policy_net = nn.Sequential(nn.Linear(embed_dim, hidden), nn.Tanh(), nn.Linear(hidden, hidden), nn.Tanh())
        self.value_net = nn.Sequential(nn.Linear(embed_dim, hidden), nn.Tanh(), nn.Linear(hidden, hidden), nn.Tanh())
        self.action_net = nn.Linear(hidden, ACTION_COUNT)
        self.value_head = nn.Linear(hidden, 1)
        for module in (self.features, self.policy_net, self.value_net):
            module.apply(lambda layer: self._initialize(layer, np.sqrt(2)))
        self._initialize(self.action_net, 0.01)
        self._initialize(self.value_head, 1.0)

    @staticmethod
    def _initialize(layer, gain):
        if isinstance(layer, nn.Linear):
            nn.init.orthogonal_(layer.weight, gain=gain)
            nn.init.constant_(layer.bias, 0)

    def vectorize(self, observation):
        validate_observation(observation, self.observation_shapes)
        return np.concatenate([observation[key].reshape(-1) for key in OBSERVATION_KEYS])

    def distribution(self, features, masks):
        encoded = self.features(features)
        logits = self.action_net(self.policy_net(encoded))
        masks = torch.as_tensor(masks, dtype=torch.bool, device=logits.device).reshape(logits.shape)
        if not masks.any(dim=-1).all():
            raise ValueError("Every decision must allow at least one action")
        # Normalize before masking to preserve the imported policy's numerics.
        logits = logits - logits.logsumexp(dim=-1, keepdim=True)
        distribution = Categorical(logits=torch.where(masks, logits, torch.full_like(logits, -1e8)))
        values = self.value_head(self.value_net(encoded)).flatten()
        return distribution, values, masks

    def evaluate(self, features, actions, masks):
        distribution, values, valid = self.distribution(features, masks)
        entropy = -torch.where(valid, distribution.logits * distribution.probs,
                               torch.zeros_like(distribution.logits)).sum(dim=-1)
        return distribution.log_prob(actions), values, entropy

    @torch.no_grad()
    def choose_action(self, observation, mask, deterministic=True, generator=None) -> PolicyDecision:
        features = torch.from_numpy(self.vectorize(observation)).unsqueeze(0)
        distribution, values, _ = self.distribution(features, mask)
        action = (distribution.probs.argmax(dim=-1) if deterministic else
                  torch.multinomial(distribution.probs, 1, generator=generator).flatten())
        return PolicyDecision(int(action.item()), float(values.item()), float(distribution.log_prob(action).item()))

    @torch.no_grad()
    def value(self, observation) -> float:
        features = torch.from_numpy(self.vectorize(observation)).unsqueeze(0)
        return float(self.value_head(self.value_net(self.features(features))).item())
