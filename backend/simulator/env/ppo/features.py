from __future__ import annotations

from typing import Any, Dict

import torch as th
import torch.nn as nn
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor


class SetTaskFeaturesExtractor(BaseFeaturesExtractor):
    """
    自定义的 SB3 特征提取器（FeaturesExtractor）。

    输入：Dict 观测，包含以下键：
    - energy:   (P, O)
    - sunlight: (P, O)
    - comm:     (P, O, P, O)
    - queue:    (P, O)
    - task_stats: (38,) 由图/集合编码器输出的固定长度向量

    做法：将前三个拓扑张量展平，拼上 task_stats，输入两层 MLP，输出固定维度（默认 256）。
    这样，即使任务数量动态变化，特征维度仍固定，满足 PPO 的输入要求。
    """

    def __init__(self, observation_space: Any, embed_dim: int = 256, phi_hidden: int = 128, rho_hidden: int = 256):
        # SB3 需要在基类中声明最终特征维度（features_dim）
        super().__init__(observation_space, features_dim=int(embed_dim))
        self.embed_dim = int(embed_dim)

        # 从 Dict 空间推断形状（不依赖具体环境对象，利于通用化）
        e_shape = tuple(observation_space.spaces["energy"].shape)
        s_shape = tuple(observation_space.spaces["sunlight"].shape)
        c_shape = tuple(observation_space.spaces["comm"].shape)
        q_shape = tuple(observation_space.spaces["queue"].shape)
        t_shape = tuple(observation_space.spaces["task_stats"].shape)

        p, o = e_shape
        # 拓扑部分展平后的维度：|energy| + |sunlight| + |comm| + |queue|
        self.topo_dim = p * o + p * o + (p * o * p * o) + (p * o)
        # 任务集合统计是固定 38 维
        self.task_dim = t_shape[0]

        in_dim = self.topo_dim + self.task_dim

        # 两层 MLP，将超长的拓扑向量 + 任务统计向量压缩到 embed_dim
        self.net = nn.Sequential(
            nn.Linear(in_dim, rho_hidden),
            nn.ReLU(),
            nn.Linear(rho_hidden, self.embed_dim),
            nn.ReLU(),
        )

    def forward(self, obs: Dict[str, th.Tensor]) -> th.Tensor:  # type: ignore[override]
        # 取出各键，并统一成 float32
        energy = obs["energy"].float()   # 可能是 (P, O) 或 (B, P, O)
        sunlight = obs["sunlight"].float()
        comm = obs["comm"].float()
        queue = obs["queue"].float()
        task_stats = obs["task_stats"].float()  # 可能是 (38,) 或 (B, 38)

        # 若无 batch 维，则补一个维度到最前（B=1），以统一处理
        if energy.dim() == 2:
            energy = energy.unsqueeze(0)
            sunlight = sunlight.unsqueeze(0)
            comm = comm.unsqueeze(0)
            queue = queue.unsqueeze(0)
            task_stats = task_stats.unsqueeze(0)

        # 将拓扑张量拉平成向量并拼接
        topo = th.cat([
            energy.flatten(start_dim=1),
            sunlight.flatten(start_dim=1),
            comm.flatten(start_dim=1),
            queue.flatten(start_dim=1),
        ], dim=1)

        x = th.cat([topo, task_stats], dim=1)
        out = self.net(x)
        return out
