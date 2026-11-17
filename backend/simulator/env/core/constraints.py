from typing import List, Dict, Tuple

from simulator.env.vars.node import Node
from simulator.schemas.task import Task
import numpy as np
import logging
from simulator.config import DEBUG, LAYER_PROCESS_SECOND_COST_GPU, STEP_PER_SLOT
from simulator.env.io.decision_manager import DecisionManager
from simulator.env.io.state_manager import StateManager
from simulator.entities.satellite_entity import SatelliteEntity

# truncation conditions

def all_tasks_overtimed(tasks: List[Task], slot: float):
    result = False
    # total_proc_time = sum(LAYER_PROCESS_SECOND_COST_GPU[i] for i in range(len(LAYER_PROCESS_SECOND_COST_GPU)))
    # total_proc_steps = total_proc_time / slot
    if len(tasks) > 0:
        result = all(t.t_end > t.ddl for t in tasks)
    return result

def any_tasks_overtimed(tasks: List[Task], slot: float):
    result = False
    # total_proc_time = sum(LAYER_PROCESS_SECOND_COST_GPU[i] for i in range(len(LAYER_PROCESS_SECOND_COST_GPU)))
    # total_proc_steps = total_proc_time / slot
    if len(tasks) > 0:
        result = any(t.t_end > t.ddl for t in tasks)
    return result

# def any_illegal_link(sm: StateManager, dm: DecisionManager, eps: float = 1e-9):
#     """Detect any active transfer decisions on links with zero/invalid capacity.

#     Updated for dict-based DecisionManager.rho where keys are
#     (up, uo, vp, vo, m) -> 1.
#     """
#     result = False

#     # if sm.is_empty() or dm.is_empty():
#         # return result

#     # Build set of unique directed links and the list of task IDs using them
#     link_to_tasks: Dict[Tuple[int, int, int, int], List[int]] = {}
#     for (up, uo, vp, vo, m), val in dm.rho.items():
#         if not val:
#             continue
#         key = (int(up), int(uo), int(vp), int(vo))
#         link_to_tasks.setdefault(key, []).append(int(m))

#     if DEBUG:
#         logging.debug(
#             "any_illegal_link(dict): unique_links=%d",
#             len(link_to_tasks),
#         )

#     if not link_to_tasks:
#         return False

#     for (up, uo, vp, vo), task_ids in link_to_tasks.items():
#         # read comm capacity for this directed link
#         try:
#             comm_f = float(sm.get_comm((up, uo), (vp, vo)))
#         except Exception as ex:
#             logging.debug(
#                 "any_illegal_link(dict): error reading sm.comm for U(%d,%d)->V(%d,%d): %s",
#                 up, uo, vp, vo, ex,
#             )
#             comm_f = 0.0

#         if comm_f <= eps:
#             # neighbors currently initialized for each endpoint (dict-based)
#             try:
#                 neighbors_u = sm.neighbors_of((up, uo))
#             except Exception as ex:
#                 neighbors_u = f"error:{ex}"
#             try:
#                 neighbors_v = sm.neighbors_of((vp, vo))
#             except Exception as ex:
#                 neighbors_v = f"error:{ex}"
#             if DEBUG:
#                 logging.warning(
#                     "Problem link: U(%d,%d) -> V(%d,%d)  tasks=%s  sm.comm=%s  neighbors_U=%s neighbors_V=%s",
#                     up, uo, vp, vo, task_ids, comm_f, neighbors_u, neighbors_v,
#                 )
#             result = True

#     return result


# termination conditions

def all_tasks_completed(tasks: List[Task]):
    """
    检查所有任务是否完成
    :param tasks: 任务列表，每个任务对象需要有 is_done 属性
    :return: 所有任务是否完成 (bool)
    """
    aim_to_complete = 100
    result = False
    # if len(tasks) > 0:
    #     result = all(t.is_done for t in tasks)
    for t in tasks:
        if t.is_done:
            aim_to_complete -= 1
    if aim_to_complete == 0:
        result = True
    return result

def any_satellite_depleted(nodes: List[SatelliteEntity]):
    """
    检查是否有卫星能量耗尽
    :param nodes: 节点列表，每个节点对象需要有 energy 属性
    :return: 是否有卫星能量耗尽 (bool)
    """
    result = False
    if len(nodes) > 0:
        result = any(n.battery <= 0 for n in nodes)
    return result

