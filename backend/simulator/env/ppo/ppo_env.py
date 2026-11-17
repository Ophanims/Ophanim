from simulator.env.ppo.policy_step import PolicyStep
import math
import numpy as np
from simulator.core.initialisation import build_static_objects, init_network, load_input_metadata
from simulator.schemas.task import Task
from simulator.env.core.logger import SystemLogger
from simulator.schemas.project import Project
import gymnasium as gym
from gymnasium import spaces
from typing import Dict, List, Tuple
from simulator.env.io.decision_manager import DecisionManager
from simulator.env.io.state_manager import StateManager
from simulator.env.core.constraints import all_tasks_completed, all_tasks_overtimed, any_satellite_depleted, any_tasks_overtimed
from simulator.config import ALL_TASK_COMPLETION_REWARD, COMP_PENALTY, ENERGY_DROWN_PENALTY, IDLE_PENALTY, TRAN_PENALTY
from simulator.env.core.entity_col import EntityCol
from simulator.env.core.task_manager import TaskManager
from simulator.env.vars.request import CompReq, TransReq
from simulator.env.core.formulation import compute_delay_penalty, compute_energy_penalty, reward_function
from simulator.env.core.operation import do_computing, do_energy_dynamic, do_energy_static, do_energy_updating, do_transferring
from simulator.env.core.observation import get_obs, get_obs_space_shape
from datetime import datetime, timedelta, timezone
from simulator.entities.earth_entity import EarthEntity
from simulator.entities.roi_entity import ROIEntity
from simulator.entities.sun_entity import SunEntity
from simulator.services.network_service import LinkSnapshot, Network
from simulator.entities.satellite_entity import SatelliteEntity
from simulator.entities.station_entity import StationEntity

class PPOEnv(PolicyStep, gym.Env):

    metadata = {"render_modes": ["human"]}

    def __init__(self, input: Project):
        super().__init__()
        # Setup logging
        self.logger = SystemLogger(name="PPOEnv")

        self.input = input

        self.t_start: datetime = datetime.now(timezone.utc)
        self.max_simulation_period: timedelta = timedelta(hours=2)  # 最大仿真时间
        self.t_end: datetime = self.t_start + self.max_simulation_period

        self.period_in_num: float = 30
        self.period: timedelta = timedelta(seconds=self.period_in_num)  # 时间步长，默认30秒
        self.max_period_numbers: int = math.ceil(self.max_simulation_period.total_seconds() / self.period_in_num)

        self.slot_in_num: float = 0.5
        self.slot: timedelta = timedelta(seconds=self.slot_in_num)  # 时间步长，默认5秒
        self.max_slot_number: int = math.ceil(self.period_in_num / self.slot_in_num)

        self.time_recorder: datetime = self.t_start
        self.period_counter: int = 0
        self.slot_counter: int = 0
        self.frame_counter: int = 0

        self.net: Network = None

        self.datetime_list: list[datetime] = []

        # Entities
        self.sat: List[SatelliteEntity] = []
        self.gs: List[StationEntity] = []
        self.roi: List[ROIEntity] = []

        self.eth: EarthEntity = None
        self.sun: SunEntity = None

        self.current_tasks: List[Task] = []
        self.current_nodes: List[SatelliteEntity] = []
        self.current_edges: List[LinkSnapshot] = []

        self.trans_reqs: List[TransReq] = []
        self.comp_reqs: List[CompReq] = []

        # Data storages
        # self._roi_datas: List[dict] = []
        self._gs_datas: List[dict] = []
        self._sat_datas: List[dict] = []
        # self._eth_datas: List[dict] = []
        # self._sun_datas: List[dict] = []

        # Entities Managers
        self.entity_collection = EntityCol(input)
        self.task_manager = TaskManager(self.entity_collection)

        # Attributes Managers
        self.state_manager = StateManager(self.entity_collection.number_of_planes, self.entity_collection.number_of_sat_per_planes)
        self.decision_manager = DecisionManager(self.entity_collection.number_of_planes, self.entity_collection.number_of_sat_per_planes)

        # 重复移动计数 (按任务 id)
        self.repeat_move_counts = {}
        # 空转计数（连续 no-op 次数，按任务 id）
        self.idle_counts = {}

        # 初始化基本参数：每步仅对一个任务决策（0-5）
        self.action_space = spaces.Discrete(6)

        # scheduling decision
        self.at_sunlit_sat = 0
        self.at_dark_sat = 0
        self.at_ground = 0

        # 固定观察空间：
        # - 依赖 StateManager 的最大维度 (P_MAX/O_MAX) 来确定拓扑张量形状；
        # - 任务集合改为置换不变的固定向量（task_stats，38维），因此 observation space 完全固定，
        #   满足 SB3 不允许变尺寸观测的要求。
        self.observation_space = get_obs_space_shape(o=self.state_manager.O_MAX, p=self.state_manager.P_MAX)
        # 当前决策的任务索引（轮询选择）
        self.current_task_idx: int = 0
        # 线性/指数限幅参数（避免惩罚爆炸）
        self.IDLE_BASE = 1.0
        self.IDLE_CAP = 5.0
        # 重复移动：使用指数型因子，前几次较小，次数多时惩罚迅速增大
        self.REPEAT_CAP = 10.0
        self.REPEAT_ALPHA = 0.4  # 指数增长速率，可根据需要微调

        self.lamda = 0.57
        self.indicators: Dict[str, Tuple[bool, bool, bool, bool]] = {}

    def setup(self, input: Project) -> None:
        """
        Reset and initialize simulation state using the provided project configuration.
        """
        self.logger.info("Setting up environment with provided project configuration.")
        metadata = load_input_metadata(input, self.max_simulation_period)
        self.t_start = metadata["t_start"]
        self.t_end = metadata["t_end"]

        self.time_recorder = metadata["time_recorder"]

        self.period = metadata["period"]
        self.max_period_numbers = metadata["max_period_numbers"]

        self.max_slot_number = math.ceil(self.period.total_seconds() / self.slot_in_num)

        self.datetime_list = metadata["datetime_list"]
        objs = build_static_objects(input, self.period, self.max_period_numbers, self.datetime_list)
        self.sat = objs['sat']
        self.gs = objs['gs']
        self.roi = objs['roi']
        self.eth = objs['eth']
        self.sun = objs['sun']
        self._sat_datas = objs['sat_datas']
        self._gs_datas = objs['gs_datas']
        self.net = init_network(input, self._sat_datas, self._gs_datas)
        self.period_update()
        self.slot_update()


    def period_update(self):
        """
        Update all entities to the specified period time.
        """
        for s in self.sat:
            s.tick(self.period_counter, self.slot_counter)

        for g in self.gs:
            g.tick(self.period_counter, self.slot_counter)

        for r in self.roi:
            r.tick(self.period_counter, self.slot_counter)

        if self.eth and self.sun:
            self.eth.tick(self.period_counter, self.slot_counter)
            self.sun.tick(self.period_counter, self.slot_counter)

        self.net._at(self.period_counter, self.slot_counter)
        self.current_edges = self.net.compute_isl_links_at(self.period_counter, self.slot_counter)
        self.current_nodes = self.sat



    def task_matching(self, tasks: List[Task]) -> None:
        """
        Match tasks to their corresponding satellite entities and add them to the satellite's task queue.
        """
        task_mapping = {}
        for task in tasks:
            p, o = task.plane_at, task.order_at
            node = next((s for s in self.sat if s.plane == p and s.order == o), None)
            if node:
                task_mapping.setdefault(node.id, []).append(task)

        for node in self.sat:
            node.matching_task_queue(task_mapping.get(node.id, []))



    def discrete_time_update(self):
        """
        Update environment state at each discrete time step.
        """
        # 帧计数 +1
        self.frame_counter += 1

        # 槽计数累加，时间推进一个 slot
        self.slot_counter += 1
        self.time_recorder = self.time_recorder + self.slot
        self.slot_update()

        # 槽数满一周期，则周期 +1，槽清零，并更新到该周期的静态对象
        if self.slot_counter >= self.max_slot_number:
            self.slot_counter = 0
            self.current_task_idx = 0

            # 周期递增并限幅在 [0, max_period_numbers-1]
            if self.period_counter < self.max_period_numbers - 1:
                self.period_counter += 1

            # 若提供了对齐到周期开始的时间表，则使用之
            if self.datetime_list:
                self.time_recorder = self.datetime_list[self.period_counter]

            # 周期切换时更新所有实体（位置/可见性/链路等）
            self.period_update()



    def slot_update(self):
        self.logger.info(f"Step {self.frame_counter}: Slot update at period {self.period_counter} slot {self.slot_counter}")
        print(f"Slot {self.frame_counter}")
        self.state_manager.clear_progress_counters()
        self.decision_manager.reset()

        for t in self.current_tasks:
            t.t_end += 1

        # do_energy_static(slot=self.slot_in_num, nodes=self.current_nodes, sm=self.SM)
        for n in self.current_nodes:
            self.indicators[n.id] = (True, True, True, True)  # pi, rho, gamma, static
            n.cost_percent = 0.0
            n.gain_percent = 0.0
            n.clear_indicators()

        self.current_tasks = self.task_manager.get_tasks_at(step=self.frame_counter)

        _finished_tasks = self.task_manager.get_all_finished_tasks()
        _all_tasks = self.task_manager.get_tasks()

        self.task_matching(self.current_tasks)

        self.logger.info(f"{len(_finished_tasks)}/{len(_all_tasks)} Tasks completed so far.")



    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.logger.info("Environment reset called.")

        # 重新生成环境
        self.period_counter = self.slot_counter = self.frame_counter = 0
        self.setup(input=self.input)
        self.period_update()

        self.time_recorder = self.t_start
        self.period_counter = 0
        self.slot_counter = 0
        self.frame_counter = 0
        self.current_task_idx = 0

        edges = self.net._all_links
        self.entity_collection.reset(self.sat, edges)

        all_nodes, all_edges = self.entity_collection.get_nodes(), self.entity_collection.get_edges()

        self.state_manager.reset()
        self.decision_manager.reset()
        self.task_manager.reset(slot=self.slot_in_num, seed=seed)
        self.repeat_move_counts = {}

        self.state_manager.setup(
            all_nodes=all_nodes,
            all_edges=all_edges
        )

        # reset 结束时返回固定形状的 Dict 观测
        obs, info = get_obs(sm=self.state_manager, dm=self.decision_manager, step=self.frame_counter)
        # # 添加 action mask
        # if len(self.current_tasks) > 0:
        #     task = self.current_tasks[self.current_task_idx]
        #     info["action_mask"] = self._get_action_mask(task)
        # else:
        #     info["action_mask"] = np.ones(6, dtype=np.int8)  # 无任务时全允许
        return obs, info



    def queue_variance(self) -> float:
        loads = []
        for n in self.current_nodes:
            if n.is_charging:
                loads.append(n.task_queue)
        var = np.std(loads) if len(loads) > 0 else 0.0
        return var

    def action_masks(self) -> np.ndarray:
        """Return current action mask for sb3-contrib ActionMasker/MaskablePPO.

        - When there are tasks, use the mask for the currently selected task.
        - When there is no task, allow all 6 actions (the policy output is ignored anyway).
        """
        if len(self.current_tasks) > 0:
            task = self.current_tasks[self.current_task_idx]
            return self._get_action_mask(task)
        return np.ones(6, dtype=np.int8)

    def _get_action_mask(self, task: Task) -> np.ndarray:
        """
        Generate action mask for current task state.
        Returns array of shape (6,) where 1 = allowed, 0 = forbidden.
        """
        mask = np.zeros(6, dtype=np.int8)
        allowed_actions = self.get_allowed_actions(task)
        # print(f"[PPOEnv] Allowed actions for task {task.id}: {allowed_actions}")
        for action in allowed_actions:
            mask[action] = 1
        return mask




    # action_masks removed: environment no longer emits or supports action masks.
    def get_valid_dirs(self, task: Task) -> List[int]:
        p, o = task.plane_at, task.order_at

        valid_dirs = []

        for a in [1, 2, 3, 4]:
            if a == 1:
                dst = ((p + 1) % self.entity_collection.number_of_planes, o)
            elif a == 2:
                dst = ((p - 1) % self.entity_collection.number_of_planes, o)
            elif a == 3:
                dst = (p, (o + 1) % self.entity_collection.number_of_sat_per_planes)
            else:
                dst = (p, (o - 1) % self.entity_collection.number_of_sat_per_planes)

            if ((p, o), dst) in self.entity_collection.edges_dict:
                valid_dirs.append(a)

        return valid_dirs

    def get_allowed_actions(self, task: Task):
        """Return the allowed action set for the given task based on its state."""
        state = self.task_manager.task_state(task)
        valid_dirs = self.get_valid_dirs(task)
        valid_actions:set[int] = set()
        if state == "under_processing":
            valid_actions = {0, 5}
        elif state == "under_transferring":
            valid_actions = {0, task.acted, 5}
        elif state == "done":
            valid_actions = {0}
        else:
            valid_actions = {0, *valid_dirs, 5}
        return valid_actions

    def validate_action(self, task: Task, act: int):
        """
        Returns (valid: bool, penalty: float, truncated: bool, reason: str)
        """
        valid = True
        allowed = self.get_allowed_actions(task)
        if act not in allowed:
            valid = False
        return valid
