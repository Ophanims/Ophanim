from simulator.env.observation_step import ObservationStep
import math
import numpy as np
import logging
import os
from simulator.schemas.project import Project
from simulator.core.initialisation import build_static_objects, init_network, load_input_metadata
from simulator.schemas.task import Task
import gymnasium as gym
from gymnasium import spaces
from typing import List
from simulator.env.io.decision_manager import DecisionManager
from simulator.env.io.state_manager import StateManager
from simulator.env.core.constraints import all_tasks_completed, all_tasks_overtimed, any_satellite_depleted
from simulator.config import ALL_TASK_COMPLETION_REWARD, ENERGY_DROWN_PENALTY, LAYER_OUTPUT_DATA_SIZE, IDLE_PENALTY, MAX_NUM_TASKS, DEBUG, LOG_OUTPUT
from simulator.env.core.entity_col import EntityCol
from simulator.env.core.task_manager import TaskManager
from simulator.env.vars.request import CompReq, TransReq
from simulator.env.core.formulation import compute_delay_penalty, compute_energy_penalty, reward_function
from simulator.env.core.operation import do_computing, do_energy_updating, do_transferring
from simulator.env.core.observation import get_obs
from datetime import datetime, timedelta, timezone
from simulator.entities.earth_entity import EarthEntity
from simulator.entities.roi_entity import ROIEntity
from simulator.entities.sun_entity import SunEntity
from simulator.services.network_service import Network
from simulator.entities.satellite_entity import SatelliteEntity
from simulator.entities.station_entity import StationEntity
from simulator.schemas.project import Project

FIRST_COMPUTE_BONUS = 0.01

class LEOEnv(ObservationStep, gym.Env):

    metadata = {"render_modes": ["human"]}

    def __init__(self, input: Project):
        super().__init__()
        # Setup logging
        self.logger = logging.getLogger("LEOEnv")
        self.logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)
        if not self.logger.handlers:
            os.makedirs(LOG_OUTPUT, exist_ok=True)
            fh = logging.FileHandler(os.path.join(LOG_OUTPUT, "env.log"))
            fh.setLevel(logging.DEBUG if DEBUG else logging.INFO)
            fmt = logging.Formatter(fmt="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
            fh.setFormatter(fmt)
            self.logger.addHandler(fh)

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

        # 初始化基本参数
        self.action_space = spaces.MultiDiscrete([6] * MAX_NUM_TASKS)

        # 初始化观察空间 based on manager max sizes (stable shape independent of current _M)
        p = self.state_manager.P_MAX
        o = self.state_manager.O_MAX
        n = self.state_manager.N_MAX
        m = self.state_manager.M_MAX

        # scheduling decision
        self.at_sunlit_sat = 0
        self.at_dark_sat = 0
        self.at_ground = 0

        obs_spaces = {
            "energy": spaces.Box(low=-np.inf, high=np.inf, shape=(p, o), dtype=np.float32),
            "sunlight": spaces.Box(low=-np.inf, high=np.inf, shape=(p, o), dtype=np.float32),
            "comm": spaces.Box(low=-np.inf, high=np.inf, shape=(p, o, p, o), dtype=np.float32),
            "location": spaces.Box(low=-np.inf, high=np.inf, shape=(m, 2), dtype=np.float32),
            "progress": spaces.Box(low=-np.inf, high=np.inf, shape=(m,), dtype=np.float32),
            "size": spaces.Box(low=-np.inf, high=np.inf, shape=(m,), dtype=np.float32),
            "workload": spaces.Box(low=-np.inf, high=np.inf, shape=(m,), dtype=np.float32),
        }
        self.observation_space = spaces.Dict(obs_spaces)

    def _align_obs(self, obs: dict) -> dict:
        """Pad or trim observation arrays to match self.observation_space shapes."""
        aligned = {}
        for k, space in self.observation_space.spaces.items():
            wanted_shape = space.shape
            # no special handling for action_mask since it is removed

            dtype = getattr(space, 'dtype', np.float32)
            arr = np.asarray(obs.get(k, np.zeros(wanted_shape, dtype=dtype)), dtype=dtype)
            # if arr has fewer dims, left-pad with batch dim removal
            if arr.shape == wanted_shape:
                aligned[k] = arr
                continue
            # create output container
            out = np.zeros(wanted_shape, dtype=dtype)
            # compute slices
            slices = tuple(slice(0, min(s, t)) for s, t in zip(arr.shape, wanted_shape))
            out[slices] = arr[tuple(slice(0, s) for s in arr.shape)]
            aligned[k] = out
        return aligned

    def setup(self, input: Project) -> None:
        """
        Reset and initialize simulation state using the provided project configuration.
        """
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
        # self._roi_datas = objs['roi_datas']
        # self._eth_datas = objs['eth_data']
        # self._sun_datas = objs['sun_data']
        self.net = init_network(input, self._sat_datas, self._gs_datas)
        self.period_update()


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

        self.net._at(self.period_counter, self.slot_counter)

        if self.eth and self.sun:
            self.eth.tick(self.period_counter, self.slot_counter)
            self.sun.tick(self.period_counter, self.slot_counter)


    def reset(self, seed=None, options=None):
        # Accept the `options` kwarg used by Gymnasium wrappers (Monitor, VecEnv).
        super().reset(seed=seed)

        # 重新生成环境
        self.period_counter = self.slot_counter = self.frame_counter = 0
        self.setup(input=self.input)
        self.period_update()

        self.time_recorder = self.t_start
        self.period_counter = 0
        self.slot_counter = 0
        self.frame_counter = 0

        edges = self.net._all_links
        self.entity_collection.reset(self.sat, edges)

        all_nodes, all_edges, all_tasks = self.entity_collection.get_nodes(), self.entity_collection.get_edges(), self.task_manager.get_tasks()

        self.state_manager.reset()
        self.decision_manager.reset()
        self.task_manager.reset(seed=seed)
        self.repeat_move_counts = {}

        self.state_manager.setup(
            all_nodes=all_nodes,
            all_edges=all_edges,
            all_tasks=all_tasks
        )

        obs, info = get_obs(sm=self.state_manager, dm=self.decision_manager, tm=self.task_manager, step=self.frame_counter)
        return self._align_obs(obs), info


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
        if state == "under_processing":
            return {0, 5}
        if state == "under_transferring":
            # allow no-op, continue same direction, or switch to compute
            return {0, task.acted, 5}
        if state == "done":
            return {0}
        # idle
        return {0, *valid_dirs, 5}

    def validate_action(self, task: Task, act: int):
        """
        Returns (valid: bool, penalty: float, truncated: bool, reason: str)
        """
        allowed = self.get_allowed_actions(task)
        # if act not in allowed:
        #     reason = "processing_interrupted" if self.TM.task_state(task) == "under_processing" else (
        #         "transfer_interrupted" if self.TM.task_state(task) == "under_transferring" else "illegal_action"
        #     )
        #     return (False, INTERRUPTION_PENALTY, True, reason)
        return (True, 0.0, False, "None")
