"""
图/集合编码器（无任务数量上限 → 固定维度向量）

核心思路：
- 对“任意数量”的任务，先构造每个任务一行的特征矩阵 X，形状 (M, F)。
- 再对 X 沿任务维度做“置换不变”的统计聚合（均值/最大/最小/标准差），并追加全局标量（任务数与密度），
  得到固定长度向量（与 M 无关）。

当前实现不依赖外部 GNN 库，仅用 StateManager 中的稀疏字典构造特征，因此鲁棒且可控。
"""

from __future__ import annotations

import math
from typing import List, Tuple

import numpy as np

from simulator.env.io.state_manager import StateManager


def _safe_std(a: np.ndarray, axis=None) -> np.ndarray:
    """安全的标准差计算：当样本量不足（<2）或为空时返回 0，避免 NaN。"""
    if a.size == 0:
        return np.zeros_like(a.mean(axis=axis)) if hasattr(a, "mean") else np.array(0.0)
    if a.shape[0] < 2 and (axis is None or (hasattr(a, "shape") and a.shape[axis] < 2)):
        return np.zeros_like(a.mean(axis=axis))
    return a.std(axis=axis)


def _clip01(x: float) -> float:
    """将数值裁剪到 [0, 1] 区间，避免异常值破坏统计量。"""
    try:
        return float(max(0.0, min(1.0, x)))
    except Exception:
        return 0.0


def _norm_or_zero(x: float, denom: float) -> float:
    """做简单归一化 x/denom，若分母为 0 则返回 0。"""
    if denom is None or denom == 0:
        return 0.0
    try:
        return float(x) / float(denom)
    except Exception:
        return 0.0


def task_feature_matrix(sm: StateManager) -> np.ndarray:
    """
    构造“每任务一行”的特征矩阵，形状 (M, F)。仅依赖 StateManager 的稀疏缓存。

        目前每个任务的特征（F=10）：
        [ p_norm, o_norm, completion, size, workload,
            node_energy, node_sunlight, deg_out_norm, avg_rate_norm, latency ]

    - p_norm/o_norm：归一化的轨道面/序号（基于 P_MAX/O_MAX），让位置信息规模稳定。
    - completion：任务进度；若数据范围在 [0, 1] 之外，会以原值保留。
    - size/workload：本步记录的大小/负载增量（来自 StateManager.size/workload）。
    - node_energy/node_sunlight：该任务所在节点的能量与日照状态。
    - deg_out_norm：该节点的“外连边”度数（邻居数）归一化，反映可通信性。
    - avg_rate_norm：到邻居的平均链路速率（数值尺度可再按需要标准化）。
    """
    # 以稳定顺序取任务 id 列表
    task_ids: List[int] = list(getattr(sm, "task_id_list", []) or [])
    M = len(task_ids)
    if M == 0:
        return np.zeros((0, 10), dtype=np.float32)

    P_MAX = int(getattr(sm, "P_MAX", 1) or 1)
    O_MAX = int(getattr(sm, "O_MAX", 1) or 1)

    rows: List[List[float]] = []
    for m in task_ids:
        # 位置信息（plane/order）与归一化
        p, o = sm.get_location(m)
        p_norm = _norm_or_zero(p, P_MAX)
        o_norm = _norm_or_zero(o, O_MAX)

        # 进度（若原值为 0~1 之间，做裁剪以增强稳定性）
        comp = float(sm.get_progress(m))
        comp = _clip01(comp) if comp <= 1.0 else float(comp)

        # 每步的任务尺度与工作量（StateManager 在 step 开始会清空增量计数）
        size = float(sm.size.get(int(m), 0.0)) if hasattr(sm, "size") else 0.0
        workload = float(sm.workload.get(int(m), 0.0)) if hasattr(sm, "workload") else 0.0

        # 任务所在节点的能量与日照状态
        node_energy = float(sm.energy.get((p, o), 0.0)) if hasattr(sm, "energy") else 0.0
        node_sun = float(sm.sunlight.get((p, o), 0)) if hasattr(sm, "sunlight") else 0.0

        # 邻接信息：外连边度数与平均速率（若无邻居则为 0）
        deg_out = 0.0
        avg_rate = 0.0
        try:
            nbrs: List[Tuple[int, int]] = sm.neighbors_of((p, o))
            deg_out = float(len(nbrs))
            if len(nbrs) > 0:
                rates = [sm.get_comm((p, o), v) for v in nbrs]
                avg_rate = float(sum(rates)) / float(len(rates)) if len(rates) > 0 else 0.0
        except (KeyError, IndexError) as exc:
            raise ValueError("Invalid neighborhood in graph observation") from exc

        # 归一化与拼接
        deg_norm = _norm_or_zero(deg_out, P_MAX * O_MAX)
        rate_norm = float(avg_rate)

        # 任务时延特征（归一化到 [0,1]）：latency=(ddl - t_end)/(ddl - t_start)
        latency = 0.0
        try:
            t_s = int(getattr(sm, "t_start_map", {}).get(int(m), 0))
            t_e = int(getattr(sm, "t_end_map", {}).get(int(m), 0))
            ddl = int(getattr(sm, "ddl_map", {}).get(int(m), 0))
            denom = max(1, ddl - t_s)
            latency = _clip01((ddl - t_e) / denom)
        except Exception:
            latency = 0.0

        rows.append([
            p_norm, o_norm, comp, size, workload, node_energy, node_sun, deg_norm, rate_norm, latency,
        ])

    return np.asarray(rows, dtype=np.float32)


def task_set_stats(sm: StateManager) -> np.ndarray:
    """
    将 (M, F) 的任务特征做“置换不变”聚合，得到固定长度的一维向量。

    统计项：
    - 按列的 mean / max / min / std → 4*F 维
    - 全局标量：任务数 M、任务密度 density=M/(P_MAX*O_MAX) → 2 维
    最终长度：4*F + 2。当前 F=10，因此输出维度为 42。
    """
    X = task_feature_matrix(sm)  # (M, F)
    if X.size == 0:
        # F=10 → 4*10 + 2 = 42 维，全 0 向量代表“无任务”状态
        return np.zeros((42,), dtype=np.float32)

    mean = X.mean(axis=0)
    _max = X.max(axis=0)
    _min = X.min(axis=0)
    _std = _safe_std(X, axis=0)

    # 全局标量
    M = float(X.shape[0])
    P_MAX = float(getattr(sm, "P_MAX", 1) or 1)
    O_MAX = float(getattr(sm, "O_MAX", 1) or 1)
    density = M / max(1.0, P_MAX * O_MAX)

    stats = np.concatenate([mean, _max, _min, _std, np.asarray([M, density], dtype=np.float32)], axis=0)
    return stats.astype(np.float32)
