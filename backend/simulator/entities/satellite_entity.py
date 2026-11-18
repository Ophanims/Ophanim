import datetime
from typing import Any, List
import numpy as np
from pydantic import BaseModel
from simulator.schemas.base import SnapshotModel
from simulator.schemas.base import XYZ, LatLon
from simulator.entities.functions.timeslot import date_to_timeslot
from simulator.services.network_service import LinkSnapshot
from simulator.config import BATTERY_MAX, COMPUTE_ENERGY_COST, STATIC_ENERGY_COST, TRANSMIT_ISL_ENERGY_COST, TRANSMIT_SGL_ENERGY_COST
from simulator.entities._satellite_modules.energy import equa_solar_income
from simulator.schemas.task import Task
from simulator.core.model import SampledModel, GeometryAction, StepContext
from simulator.core.actions import SatelliteAction

class SatelliteSnapshot(SnapshotModel):
    processor_clock_frequency_ghz: float | None = None
    # spatial
    id: str
    plane: int
    order: int
    dimensions: List[float]
    pos: XYZ
    loc: LatLon
    velocity_vector: XYZ
    solar_vector: XYZ

    # imagery
    img_corners_pos: List[XYZ]
    img_corners_loc: List[LatLon]

    # energy
    battery_percent: float
    cost_percent: float
    gain_percent: float

    #memory
    task_queue: int = 0
    max_task_queue: int = 5
    task_queue_percent: float = 0.0

    # indicators
    is_observing: bool
    is_communicating_sgl: bool
    is_processing: bool
    is_communicating_isl: bool
    is_charging: bool


class SatelliteEntity(SampledModel):
    def __init__(
        self,
        time_series: dict[str, Any],
    ):
        # === 卫星基本参数 ===
        # 卫星时序数据
        self.time_series: dict[str, Any] = time_series
        # 卫星 ID
        self.id: str = time_series['id']
        # 卫星编号
        self.order: int = time_series['order']
        # 卫星所在轨道平面编号
        self.plane: int = time_series['plane']
        # 卫星扫掠长度（单位：m）
        self.sl: float = time_series['swath_length']
        # 卫星卫星尺寸（长，宽，高）（单位：m）
        self.dimensions: tuple[float, float, float] = (0.3, 0.3, 0.3)

        # === 空间与姿态 ===
        # 1. ECEF坐标
        self.pos: XYZ = XYZ(x=0.0, y=0.0, z=0.0)
        # 2. 地理坐标（纬度，经度）
        self.loc: LatLon = LatLon(lat=0.0, lon=0.0)
        # 3. 图像角点 ECEF 坐标
        self.img_corners_pos: List[XYZ] = []
        # 4. 图像角点 地理坐标
        self.img_corners_loc: List[LatLon] = []
        # 5. 地面速度（单位：度/秒）
        self.v: float = 0.0
        self.velocity_vector: np.ndarray = np.array([0.0, 0.0, -1.0])
        self.solar_vector: np.ndarray = np.array([0.0, 0.0, -1.0])

        # === Indicator 状态 ===
        self.is_charging = False            # 处于阳照区
        self.is_processing = False          # 正在处理
        self.is_observing = False           # 正在观测
        self.is_communicating_isl = False   # 正在通信
        self.is_communicating_sgl = False   # 可与地面通信

        # === 电池与能源 ===
        self.battery: float = BATTERY_MAX     # 当前电池电量
        self.battery_ratio: float = 1.0    # 当前电池电量百分比
        self.gain_percent: float = 0.0
        self.cost_percent: float = 0.0

        #memory
        self.task_list: List[Task] = []
        self.task_queue: int = 0
        self.max_task_queue: int = 10
        self.task_queue_percent: float = 0.0

        # === 通信模块 ===
        self.connections: dict[str, LinkSnapshot] = {}  # 当前连接的链路信息

    def tick(self, period_counter: int, slot_counter: int) -> None:
        self._at(period_counter, slot_counter)

    def transition(self, action: SatelliteAction | GeometryAction, context: StepContext) -> SatelliteSnapshot:
        if isinstance(action, GeometryAction):
            return super().transition(action, context)
        self.is_processing = action.is_processing
        self.is_communicating_isl = action.is_communicating_isl
        self.is_communicating_sgl = action.is_communicating_sgl
        if action.update_energy:
            # Indicators describe activity during this interval, including work
            # completed at its end; charge/draw happen exactly once per slot.
            self.energy_step(context.dt_s)
            self.is_processing = action.is_processing
            self.is_communicating_isl = action.is_communicating_isl
            self.is_communicating_sgl = action.is_communicating_sgl
        if action.geometry is not None:
            self._at(action.geometry.period_counter, action.geometry.slot_counter)
            self.is_communicating_sgl = action.is_communicating_sgl
        return self.snapshot()

    # def add_task_to_queue(self, task: Task) -> None:
    #     if self.task_queue < self.max_task_queue:
    #         self.task_list.append(task)
    #         self.task_queue += 1
    #         self.task_queue_percent = self.task_queue / self.max_task_queue

    # def remove_task_from_queue(self, task: Task) -> None:
    #     if self.task_queue > 0:
    #         self.task_list.remove(task)
    #         self.task_queue -= 1
    #         self.task_queue_percent = self.task_queue / self.max_task_queue

    def matching_task_queue(self, tasks: List[Task]) -> None:
        self.task_list = tasks
        self.task_queue = len([t for t in self.task_list if not t.is_done])
        self.task_queue_percent = self.task_queue / self.max_task_queue

    def energy_step(self, dt: float) -> None:
        g = self.charge(dt)
        c1 = self.discharge_static(dt)
        c2 = self.discharge_dynamic(dt)
        self.gain_percent = g * 100
        self.cost_percent = (c1 + c2) * 100
        self.clear_indicators()

    def clear_indicators(self) -> None:
        self.is_processing = False
        self.is_observing = False
        self.is_communicating_isl = False
        self.is_communicating_sgl = False

    def charge(self, dt: float) -> float:
        gain = equa_solar_income(
            dt=dt,
            sat_pos=self.pos,
            dimensions=self.dimensions,
            solar_vector=self.solar_vector,
            velocity=self.velocity_vector,
            mu_t=1 if self.is_charging else 0
        )
        # print(f"Satellite {self.id} charging for dt={dt}s: gain={gain:.2f}Wh")
        # 44.25Wh左右
        self.battery = min(self.battery + gain, BATTERY_MAX)
        self.battery_ratio = (self.battery / BATTERY_MAX)
        return gain / BATTERY_MAX

    def discharge_static(self, dt: float) -> float:
        cost = dt * STATIC_ENERGY_COST
        self.battery = max(self.battery + cost, 0)
        self.battery_ratio = (self.battery / BATTERY_MAX)
        # print(f"dt {dt} Static discharge for satellite {self.id}: cost={cost:.2f}, battery={self.battery:.2f}, percent={self.battery_percent:.2f}%")
        return cost / BATTERY_MAX

    def discharge_dynamic(self, dt: float) -> None:
        cost = dt * (
            self.is_communicating_sgl * TRANSMIT_SGL_ENERGY_COST +
            self.is_communicating_isl * TRANSMIT_ISL_ENERGY_COST +
            self.is_processing * COMPUTE_ENERGY_COST
            )
        self.battery = max(self.battery + cost, 0)
        self.battery_ratio = (self.battery / BATTERY_MAX)
        return cost / BATTERY_MAX

    def discharge_isl(self, dt: float) -> float:
        cost = dt * (self.is_communicating_isl * TRANSMIT_ISL_ENERGY_COST)
        self.battery = max(self.battery + cost, 0)
        self.battery_ratio = (self.battery / BATTERY_MAX)
        return cost / BATTERY_MAX

    def discharge_compute(self, dt: float) -> float:
        cost = dt * (self.is_processing * COMPUTE_ENERGY_COST)
        self.battery = max(self.battery + cost, 0)
        self.battery_ratio = (self.battery / BATTERY_MAX)
        return cost / BATTERY_MAX

    def _at(self, period_counter: int, slot_counter: int) -> None:
        # 更新位置
        pos = self.time_series["space_xyz"][period_counter]
        self.pos = XYZ(x=pos[0], y=pos[1], z=pos[2])

        # 更新地理坐标
        lat, lon = self.time_series["subpoint_latlon"][period_counter]
        self.loc = LatLon(lat=lat, lon=lon)

        # 更新地面速度
        self.v = self.time_series["azimuth"][period_counter]

        # 更新充电状态
        self.is_charging = self.time_series["is_sunlit"][period_counter]

        # 更新图像角点位置和地理坐标
        self.img_corners_pos = [
            XYZ(x=corner[0], y=corner[1], z=corner[2])
            for corner in self.time_series["footprint_corners_xyz"][period_counter]
        ]
        self.img_corners_loc = [
            LatLon(lat=corner[0], lon=corner[1])
            for corner in self.time_series["footprint_corners_latlon"][period_counter]
        ]

        self.is_communicating_sgl = any(link.type in ('UL', 'DL') for link in self.connections.values())

        self.solar_vector = self.time_series["solar_vector"][period_counter]

        # 获取单位化速度向量（-z方向，用于论文坐标系）
        self.velocity_vector = self.time_series["velocity_vector"][period_counter]

    def snapshot(self) -> SatelliteSnapshot:
        return SatelliteSnapshot(
            # spatial
            id=self.id,
            plane=self.plane,
            order=self.order,
            dimensions=self.dimensions,
            pos=self.pos,
            loc=self.loc,
            velocity_vector=XYZ(x=self.velocity_vector[0],
                    y=self.velocity_vector[1],
                    z=self.velocity_vector[2]),
            solar_vector=XYZ(x=self.solar_vector[0],
                    y=self.solar_vector[1],
                    z=self.solar_vector[2]),
            # imagery
            img_corners_pos=self.img_corners_pos,
            img_corners_loc= self.img_corners_loc,
            # Energy
            battery_percent=self.battery_ratio * 100,
            cost_percent=self.cost_percent,
            gain_percent=self.gain_percent,
            # indicators
            is_observing=bool(self.is_observing),
            is_communicating_sgl=bool(self.is_communicating_sgl),
            is_processing=bool(self.is_processing),
            is_communicating_isl=bool(self.is_communicating_isl),
            is_charging=bool(self.is_charging),
            # memory
            task_queue=self.task_queue,
            task_queue_percent=self.task_queue_percent,
            max_task_queue=self.max_task_queue,
        ).model_copy(deep=True)

    def sunlit_ratio(self, start: int = 0, delta: int = 1, step: int = 1) -> float:
        """
        计算在给定采样步长下的日照占比（百分比）。
        """
        end = start + delta if delta > 0 else None
        sun_series = self.time_series.get("is_sunlit")
        # 显式判空与长度/size判断，避免 numpy 的布尔歧义
        if sun_series is None:
            return 0.0

        import numpy as np
        n = len(sun_series)
        s = max(0, start)
        e = n if end is None else max(0, min(end, n))
        if step <= 0 or s >= e:
            return 0.0

        # 采样统计
        total = ((e - s) + (step - 1)) // step  # 采样点数量
        sun = np.asarray(sun_series[s:e:step], dtype=bool).sum()
        return (float(sun) / float(total)) if total > 0 else 0.0

    def serialize(self) -> dict:
        return self.snapshot().model_copy(deep=True).model_dump(mode="json")
