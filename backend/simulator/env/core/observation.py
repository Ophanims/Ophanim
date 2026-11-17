import numpy as np
from typing import Dict, Tuple
from gymnasium import spaces
from simulator.env.io.decision_manager import DecisionManager
from simulator.env.io.state_manager import StateManager
from simulator.env.core.task_manager import TaskManager
from simulator.env.core.graph_encoder import task_set_stats

def get_obs_space_shape(o: int, p: int) -> Dict[str, Tuple[int, ...]]:
    """
    返回“固定形状”的观测空间（Dict）。
    设计变化：
    - 原先随任务数 M 变化的数组（location/progress/size/workload/task_mask）被移除，
        改为单个固定长度的 `task_stats` 向量（置换不变统计，长度 38）。
    - 拓扑相关的张量（energy/sunlight/comm/queue）仍保持固定形状：
        · energy:   (P, O)
        · sunlight: (P, O)
        · comm:     (P, O, P, O)
        · queue:    (P, O)
    这样即可满足 SB3 对 observation space 固定的要求，同时支持任意数量任务。
    """
    obs_spaces = {
        # 能量（节点层面），形状 (P, O)
        "energy":     spaces.Box(low=-np.inf, high=np.inf, shape=(p, o), dtype=np.float32),
        # 日照（节点层面），形状 (P, O)
        "sunlight":   spaces.Box(low=-np.inf, high=np.inf, shape=(p, o), dtype=np.float32),
        # 通信能力（有向边容量），形状 (P, O, P, O)
        "comm":       spaces.Box(low=-np.inf, high=np.inf, shape=(p, o, p, o), dtype=np.float32),
        # 节点任务负载/队列百分比，形状 (P, O)
        "queue":      spaces.Box(low=-np.inf, high=np.inf, shape=(p, o), dtype=np.float32),
        # 任务集合的置换不变统计特征，固定 42 维（4*F+2，F=10）
        "task_stats": spaces.Box(low=-np.inf, high=np.inf, shape=(42,), dtype=np.float32),
    }
    return spaces.Dict(obs_spaces)

def _pad_to_space(obs_dict: dict, obs_space: spaces.Dict) -> dict:
    """
    将原始字典 obs_dict 的各个字段自动对齐到 obs_space 指定的形状与 dtype。
    - 若某个键不存在或 shape 不匹配，则填充/截断到目标形状。
    - 这样可以保证输出始终满足 gymnasium 的空间约束。
    - 返回的所有值都是 numpy array，无论输入类型如何。
    """
    aligned = {}
    for k, space in obs_space.spaces.items():
        shape = space.shape
        dtype = getattr(space, "dtype", np.float32)
        src = obs_dict.get(k)

        # 转换为 numpy array
        if src is None:
            a = np.zeros(shape, dtype=dtype)
        else:
            a = np.asarray(src, dtype=dtype)

        # 形状检查与对齐
        if a.shape == shape:
            aligned[k] = a
            continue

        # 形状不匹配：创建目标形状的容器，按元素复制
        out = np.zeros(shape, dtype=dtype)
        slices_out = tuple(slice(0, min(a_dim, s_dim)) for a_dim, s_dim in zip(a.shape, shape))
        slices_in = tuple(slice(0, s.stop) for s in slices_out)
        out[slices_out] = a[slices_in]
        aligned[k] = out

    return aligned

def get_obs(sm: StateManager, dm: DecisionManager, step: int):
    """
    生成环境观测：
    - beta（从 StateManager）提供拓扑密集张量；
    - 任务集合通过 `task_set_stats` 压缩为固定 42 维；
    - 与 SB3 要求一致，整个 Dict 形状固定。
    返回的 obs 是 dict of fixed-shape numpy arrays，满足 observation_space 要求。
    """
    beta_t = sm.report(step)

    # 固定形状字段（拓扑 + 任务集合统计）
    raw_obs = {
        "energy":   beta_t.get("energy"),
        "sunlight": beta_t.get("sunlight"),
        "comm":     beta_t.get("comm"),
        "queue":    beta_t.get("queue"),
        # 置换不变的 42 维任务统计特征
        "task_stats": task_set_stats(sm),
    }

    # 构造固定空间并统一对齐（防止 dtype 或 shape 偏差）
    # _pad_to_space 确保所有值都是 numpy array，形状和 dtype 与 obs_space 一致
    obs_space = get_obs_space_shape(o=sm.O_MAX, p=sm.P_MAX)
    obs = _pad_to_space(raw_obs, obs_space)

    # 验证所有字段都是 numpy array
    for k, v in obs.items():
        if not isinstance(v, np.ndarray):
            raise TypeError(f"obs['{k}'] must be numpy array, got {type(v)}")

    # alpha（DecisionManager 的稀疏决策快照）放在 info 中，便于调试/可视化
    alpha_t = dm.report(step)
    info = {"alpha": alpha_t, "beta": beta_t, "step": step}
    return obs, info
