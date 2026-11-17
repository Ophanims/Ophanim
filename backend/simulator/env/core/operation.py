from typing import List
from simulator.env.io.state_manager import StateManager
from simulator.entities.satellite_entity import SatelliteEntity
from typing import List
from simulator.env.io.decision_manager import DecisionManager
from simulator.config import BATTERY_MAX, COMP_PENALTY, COMPUTE_ENERGY_COST, COMPUTE_ENERGY_COST, LAYER_COMPLETION_REWARD, LAYER_OUTPUT_DATA_SIZE, LAYER_PROCESS_SECOND_COST_GPU, MAX_NUM_LAYERS, INDIVIDUAL_COMPLETION_REWARD, INDIVIDUAL_COMPLETION_REWARD, OVERTIME_PENALTY, TRAN_PENALTY, TRANSMIT_ISL_ENERGY_COST
from simulator.env.vars.request import CompReq, TransReq
from simulator.schemas.task import Task

ENERGY_PENALTY_SCALE = 10.0

def do_computing(
    slot: float,
    sm: StateManager,
    dm: DecisionManager,
    req: CompReq,
    reqs: List[CompReq],
):
    rewards = 0.0
    # LAYER_PROCESS_STEP_COST = [math.ceil(i * STEP_PER_SECOND) for i in LAYER_PROCESS_SECOND_COST_GPU]
    # 处理每个传输请求
    task = req.task
    node = req.node

    node.is_processing = True
    dm.write_pi(p=node.plane, o=node.order, m=task.id, value=True)

    # 得到当前需要计算的总工作量
    n = task.layer_id
    target = LAYER_PROCESS_SECOND_COST_GPU[n] / slot

    # 更新计算进度 (记录前进度以计算增量奖励)
    task.workload_done += 1
    task.workload_percent = task.workload_done / target

    # 加上每次计算奖励
    # energy_consumed = COMPUTE_ENERGY_COST * slot # COMPUTE_ENERGY_COST is minus
    # energy_ratio = energy_consumed / BATTERY_MAX
    # rewards += energy_ratio * ENERGY_PENALTY_SCALE
    rewards += COMP_PENALTY

    # 检查是否完成计算
    if task.workload_done >= target:
        # 计算完成：进入下一层
        task.layer_id += 1
        task.workload_done = 0
        task.workload_percent = 0.0

        reqs.remove(req)

        # 正确的完成度应基于更新后的 task.layer_id
        _all_workload = sum(LAYER_PROCESS_SECOND_COST_GPU) / slot
        _done = sum(LAYER_PROCESS_SECOND_COST_GPU[i] / slot for i in range(0, task.layer_id))
        task.completion = _done / _all_workload

        # 加上层完成奖励
        rewards += LAYER_COMPLETION_REWARD

        # 检查任务是否完成
        if task.layer_id >= MAX_NUM_LAYERS:
            task.is_done = True
            rewards += INDIVIDUAL_COMPLETION_REWARD

            # 如果完成了但超时了，把奖励扣掉一部分
            if task.t_end > task.ddl:
                rewards += OVERTIME_PENALTY

    # 更新任务完成度到StateManager
    sm.write_progress(m=task.id, value=task.completion)
    # 记录当前任务累计计算进度（按任务）
    sm.write_workload(m=task.id, value=task.workload_percent)

    return rewards


def do_transferring(
    slot: float,
    sm: StateManager,
    dm: DecisionManager,
    req: TransReq,
    reqs: List[TransReq],
):
    rewards = 0.0

    # 处理每个传输请求
    tasks: List[Task] = [req.task for req in reqs]
    task = req.task
    dst = req.dst
    src = req.src

    # 获取任务当前层数和位置
    # src = sm.get_location(m)

    src.is_communicating_isl = True
    dm.write_rho(u=(src.plane, src.order), v=(dst.plane, dst.order), m=task.id, value=True)

    # 得到当前需要传输的总数据量
    n = task.layer_id
    src_tuple = (task.plane_at, task.order_at)
    target_data_to_send = LAYER_OUTPUT_DATA_SIZE[n]
    # print(f"Task {m} (n={n}) transferring data {target_data_to_send} from {src} to {dst}")

    # 获取当前通信速率
    comm_capacity = sm.get_comm(u=src_tuple, v=(dst.plane, dst.order))
    if comm_capacity == 0:
        return rewards  # 无通信能力，跳过

    # 得到使用该链路的所有任务列表
    users_uv = dm.get_rho_by_uv(u=src_tuple, v=(dst.plane, dst.order))  # Dict[m, bool]
    # 得到使用该链路的所有任务列表（反向）
    users_vu = dm.get_rho_by_uv(u=(dst.plane, dst.order), v=src_tuple)  # Dict[m, bool]
    # 得到所有使用该链路的任务集合（统一链路双向）
    all_ms = set(users_uv.keys()) | set(users_vu.keys())

    # 计算所有任务的总数据量
    target_list = []
    for m_other in all_ms:
        if users_uv.get(m_other, False) or users_vu.get(m_other, False):
            _t = next((task for task in tasks if task.id == m_other), None)
            if _t is None:
                continue
            layer_idx = _t.layer_id
            target_list.append(LAYER_OUTPUT_DATA_SIZE[layer_idx])
    sum_of_data = sum(target_list)

    # 计算带宽比例（本地任务数据量占比）
    bandwidth_ratio = target_data_to_send / sum_of_data if sum_of_data > 0 else 0
    # 计算此步可传输的数据量
    data_this_step = comm_capacity * slot * bandwidth_ratio
    # 更新传输进度，位置不变
    task.data_sent += data_this_step
    task.data_percent = task.data_sent / target_data_to_send

    # 加上每次传输惩罚
    # energy_consumed = TRANSMIT_ISL_ENERGY_COST * slot
    # energy_ratio = energy_consumed / BATTERY_MAX
    # rewards += energy_ratio * ENERGY_PENALTY_SCALE
    rewards += TRAN_PENALTY

    # 检查是否完成传输
    if task.data_sent >= target_data_to_send:

        # 传输完成，更新任务位置 (write destination coordinates)
        task.plane_at, task.order_at = dst.plane, dst.order

        # 传输完成，更新任务进度
        task.data_sent = 0.0
        task.data_percent = 0.0
        # sm.write_size(m=m, value=0.0)
        reqs.remove(req)

    # 写入按任务的累计传输进度（比例）
    sm.write_size(m=task.id, value=task.data_percent)
    # 更新任务位置
    sm.write_location(m=task.id, value=(task.plane_at, task.order_at))

    return rewards


def do_energy_updating(slot: float, nodes: List[SatelliteEntity], sm: StateManager):
    for n in nodes:
        n.energy_step(dt=slot)
        sm.write_energy(n.plane, n.order, n.battery_ratio)

def do_energy_static(slot: float, nodes: List[SatelliteEntity], sm: StateManager):
    for n in nodes:
        n.charge(dt=slot)
        n.discharge_static(dt=slot)
        n.clear_indicators()
        sm.write_energy(n.plane, n.order, n.battery_ratio)

def do_energy_dynamic(slot: float, nodes: List[SatelliteEntity], sm: StateManager):
    for n in nodes:
        n.discharge_dynamic(dt=slot)
        n.clear_indicators()
        sm.write_energy(n.plane, n.order, n.battery_ratio)
