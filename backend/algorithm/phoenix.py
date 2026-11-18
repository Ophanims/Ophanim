from __future__ import annotations


import math
import numpy as np
from util.const import EPHEMERIS
from datetime import timedelta
from typing import Any, Dict, List, Set, TYPE_CHECKING, Tuple


from algorithm.algo import Algorithm
from core.simulation_clock import CLOCK
from core.session_context import WORLD
from status.mission_status import MissionPhase, MissionStatus
from util.time_utils import to_skyfield_time
from simulator.core.model import StepContext
from simulator.core.actions import MissionAction


if TYPE_CHECKING:
   from entity.mission import Mission
   from topology.link import Link
   from entity.sat import Satellite


class PhoenixAlgorithm(Algorithm):
   """Reproduction of the paper workflow:
   1) Sunlight-aware Orbit Assignment
   2) Orbit-based Offloading
   3) Processing Arrangement
   """

   def __init__(self, world=None, clock=None):
       self.world = world if world is not None else WORLD
       self.clock = clock if clock is not None else CLOCK
       self.prediction_cache = self.world.prediction_cache

   def observe(self, satellite: "Satellite") -> Dict[str, Any]:
       pending_tasks = [
           m
           for m in self.world.missions
           if m.position.addr == satellite.addr
           and m.status == MissionStatus.IDLE
           and m.phase == MissionPhase.UPLOADING
           and m.start_slot >= self.clock.current_slot
       ]


       all_active_tasks = [
           m for m in self.world.missions
           if m.status not in {MissionStatus.COMPLETED, MissionStatus.FAILED}
       ]


       alt_set = self._sunlight_aware_orbit_assignment(self.world.satellites, all_active_tasks)


       return {
           "pending_tasks": pending_tasks,
           "all_active_tasks": all_active_tasks,
           "alt_set": alt_set,
           "current_slot": self.clock.current_slot,
       }


   def decide(self, satellite: "Satellite", state: Dict[str, Any]) -> List[Dict[str, Any]]:
       actions = []
       pending_tasks: List[Mission] = state.get("pending_tasks", [])
       if not pending_tasks:
           return actions


       # 深拷贝或转为列表，使其在循环中可变
       dynamic_active_tasks = list(state.get("all_active_tasks", []))


       sorted_tasks = sorted(pending_tasks, key=lambda tk: (tk.deadline_slot, tk.id))
       for task in sorted_tasks:
          
           dst_addr, schedule = self._orbit_based_offloading(
               src_sat=satellite,
               new_task=task,
               alt_set=state.get("alt_set", {}),
               all_active_tasks=dynamic_active_tasks, # 传入动态队列
           )
          
           # 如果决定本地处理，立即更新动态队列，让后续任务能感知到资源占用
           if dst_addr == satellite.addr:
               if task not in dynamic_active_tasks:
                   dynamic_active_tasks.append(task)
          
           actions.append({
               "task_id": task.id,
               "dst": dst_addr,
               "schedule": schedule,
           })


       return actions


   def act(self, satellite: "Satellite", actions: List[Dict[str, Any]]) -> None:
       for action in actions:
           task_id = action.get("task_id")
           dst_addr = action.get("dst")
           if task_id is None or dst_addr is None:
               return


           mission = next((m for m in self.world.missions if m.id == task_id), None)
           if mission is None:
               return


           if dst_addr == satellite.addr:
               mission.transition(MissionAction(True), StepContext(self.clock.current_datetime, self.clock.SLOT, self.clock.current_slot))
               return


           mission.transition(MissionAction(False), StepContext(self.clock.current_datetime, self.clock.SLOT, self.clock.current_slot))


   # ---------------------------
   # Algorithm 1
   # ---------------------------
   def _sunlight_aware_orbit_assignment(
       self,
       sats: List["Satellite"],
       tasks: List[Mission],
   ) -> Dict[int, Set[int]]:
       if not sats:
           return {}


       _, cyc_slots = sats[0].get_orbital_cycle()
       cyc_slots = max(int(cyc_slots or 0), 1)


       orbits: Dict[int, List["Satellite"]] = {}
       for s in sats:
           orbits.setdefault(int(s.plane), []).append(s)


       orbit_ids = sorted(orbits.keys())
       t0 = self.clock.current_slot


       arrivals: Dict[str, List[Mission]] = {}
       for tk in tasks:
           src_addr = getattr(getattr(tk, "src", None), 'addr', None)
           if src_addr is None:
               continue
           if t0 <= int(getattr(tk, "start_slot", t0)) <= t0 + cyc_slots - 1:
               arrivals.setdefault(src_addr, []).append(tk)


       sunlit: Dict[int, int] = {oid: 0 for oid in orbit_ids}
       task_demand: Dict[int, int] = {oid: 0 for oid in orbit_ids}


       for oid in orbit_ids:
           for s in orbits[oid]:
               sunlit[oid] += self._sunlit_slots_for_sat(s, start_slot=t0, slots_num=cyc_slots)


               s_tasks = arrivals.get(s.addr, [])
               for tk in s_tasks:
                   task_demand[oid] += self._task_processing_slots(s, tk)


       total_task = sum(task_demand.values())
       total_sunlit = sum(sunlit.values())


       target: Dict[int, int] = {oid: 0 for oid in orbit_ids}
       if total_task > 0:
           for oid in orbit_ids:
               w_i = task_demand[oid] / total_task
               target[oid] = int(w_i * total_sunlit) - sunlit[oid]


       idle_orbits = [oid for oid in orbit_ids if task_demand[oid] == 0]
       alt_set: Dict[int, Set[int]] = {}


       for oid in orbit_ids:
           if target[oid] < 0:
               alt_set[oid] = {oid}
               continue


           subset = self._knapsack(idle_orbits, sunlit, target[oid])
           alt_set[oid] = {oid}.union(subset)
           idle_orbits = [x for x in idle_orbits if x not in subset]


       return alt_set


   # ---------------------------
   # Algorithm 2
   # ---------------------------
   def _orbit_based_offloading(
       self,
       src_sat: "Satellite",
       new_task: Mission,
       alt_set: Dict[int, Set[int]],
       all_active_tasks: List[Mission],
   ) -> Tuple[str, Dict[int, int] | None]:
       dl_link, t_gs = self._get_available_gs(src_sat)
       ddl_slot = self._deadline_slot(new_task)


       if dl_link is not None:
           available_cap = max(dl_link.capacity, 1e-9)
           trans_slots = math.ceil(new_task.data_size / available_cap)
           if t_gs + trans_slots <= ddl_slot:
               return dl_link.dst.addr, None


       local_tasks = [
           m
           for m in all_active_tasks
           if getattr(m.position, 'addr', None) == src_sat.addr and m.status != MissionStatus.COMPLETED
       ]
       if new_task not in local_tasks:
           local_tasks.append(new_task)


       x_hat, flag_sun = self._processing_arrangement(src_sat, self.clock.current_slot, local_tasks)
       if flag_sun == 1:
           return src_sat.addr, x_hat


       candidate_orbits = alt_set.get(int(src_sat.plane), {int(src_sat.plane)})


       orbit_load: Dict[int, int] = {}
       orbit_sun: Dict[int, int] = {}
       for oid in candidate_orbits:
           sats_in_orbit = [s for s in self.world.satellites if int(s.plane) == int(oid)]
           orbit_load[oid] = 0
           for s in sats_in_orbit:
               for m in all_active_tasks:
                   if getattr(m.position, 'addr', None) == s.addr:
                       orbit_load[oid] += self._task_processing_slots(s, m)
           orbit_sun[oid] = max(
               1,
               sum(
                   self._sunlit_slots_for_sat(s, self.clock.current_slot, max(1, self._task_processing_slots(s, new_task)))
                   for s in sats_in_orbit
               ),
           )


       best_orbit = min(candidate_orbits, key=lambda oid: orbit_load.get(oid, 0) / max(1, orbit_sun.get(oid, 1)))


       sats_in_best_orbit = [s for s in self.world.satellites if int(s.plane) == int(best_orbit)]
       if not sats_in_best_orbit:
           return src_sat.addr, x_hat


       dst_sat = max(sats_in_best_orbit, key=self._query_energy)
       if dst_sat.addr == src_sat.addr:
           return src_sat.addr, x_hat
       return dst_sat.addr, None


   # ---------------------------
   # Algorithm 3
   # ---------------------------
   def _processing_arrangement(
       self,
       sat: "Satellite",
       start_slot: int,
       tasks: List[Mission],
   ) -> Tuple[Dict[int, int], int]:
       if not tasks:
           return {}, 1


       tasks_sorted = sorted(tasks, key=self._deadline_slot)
       n = len(tasks_sorted)


       cp = [self._task_processing_slots(sat, tk) for tk in tasks_sorted]
       ddl = [self._deadline_slot(tk) for tk in tasks_sorted]


       t_latest = [0] * n
       t_latest[n - 1] = ddl[n - 1] - cp[n - 1]
       for k in range(n - 2, -1, -1):
           t_latest[k] = min(ddl[k], t_latest[k + 1]) - cp[k]


       flag_sun = 1
       t_earliest = start_slot
       schedule: Dict[int, int] = {}


       for k, tk in enumerate(tasks_sorted):
           t_sunlit = self._find_next_sunlit_slot(sat, t_earliest)


           if t_sunlit <= t_latest[k]:
               start_k = t_sunlit
           else:
               start_k = t_latest[k]
               flag_sun = 0


           schedule[tk.id] = int(start_k)
           t_earliest = min(t_sunlit, t_latest[k]) + cp[k]


       return schedule, flag_sun


   # ---------------------------
   # Helpers
   # ---------------------------
   def _ensure_cache_epoch(self) -> None:
       current_slot = int(self.clock.current_slot or 0)
       if self.prediction_cache.slot_anchor != current_slot:
           self.prediction_cache.slot_anchor = current_slot
           self.prediction_cache.slot_times.clear()
           self.prediction_cache.sunlit.clear()


   def _slot_to_time(self, slot: int):
       self._ensure_cache_epoch()
       slot_i = int(slot)
       cached = self.prediction_cache.slot_times.get(slot_i)
       if cached is not None:
           return cached

       if self.clock.current_datetime is None:
           return self.clock.current_time
       delta_slots = max(0, int(slot) - int(self.clock.current_slot))
       dt = self.clock.current_datetime + timedelta(seconds=delta_slots * self.clock.SLOT)
       t = to_skyfield_time(dt)
       self.prediction_cache.slot_times[slot_i] = t
       return t


   def _is_sunlit_cached(self, sat: "Satellite", slot: int) -> bool:
       self._ensure_cache_epoch()
       slot_i = int(slot)
       key = (sat.addr, slot_i)
       cached = self.prediction_cache.sunlit.get(key)
       if cached is not None:
           return cached

       t = self._slot_to_time(slot_i)
       value = bool(sat.is_sunlit(t))
       self.prediction_cache.sunlit[key] = value
       return value


   def _sunlit_slots_for_sat(self, sat: "Satellite", start_slot: int, slots_num: int) -> int:
       if slots_num <= 0:
           return 0
       self._ensure_cache_epoch()
       slots = range(start_slot, start_slot + slots_num)
       if all((sat.addr, slot) in self.prediction_cache.sunlit for slot in slots):
           return sum(self.prediction_cache.sunlit[(sat.addr, slot)] for slot in slots)
       offsets = np.maximum(0, np.arange(start_slot, start_slot + slots_num) - self.clock.current_slot)
       times = self.clock.current_time.ts.tt_jd(self.clock.current_time.tt + offsets * self.clock.SLOT / 86400)
       values = sat.at(times).is_sunlit(EPHEMERIS)
       self.prediction_cache.sunlit.update({(sat.addr, slot): bool(value) for slot, value in zip(slots, values)})
       return int(np.count_nonzero(values))


   @staticmethod
   def _deadline_slot(task) -> int:
       return int(task.deadline_slot)


   def _task_processing_slots(self, sat: "Satellite", task: Mission) -> int:
       freq = sat.processor_clock_frequency_ghz
       workload = task.calc_total_workload()
       slots = math.ceil(workload / (freq * 1e9 * max(self.clock.SLOT, 1)))
       return max(slots, 1)


   def _find_next_sunlit_slot(self, sat: "Satellite", earliest_slot: int) -> int:
       _, cyc_slots = sat.get_orbital_cycle()
       horizon = max(int(cyc_slots or 0), 1)
       for tau in range(earliest_slot, earliest_slot + horizon):
           if self._is_sunlit_cached(sat, tau):
               return tau
       return earliest_slot


   def _knapsack(self, idle_orbits: List[int], sunlit_values: Dict[int, int], target_value: int) -> Set[int]:
       if target_value <= 0 or not idle_orbits:
           return set()


       items = sorted(idle_orbits, key=lambda oid: sunlit_values.get(oid, 0), reverse=True)
       chosen: Set[int] = set()
       acc = 0
       for oid in items:
           if acc >= target_value:
               break
           val = max(0, int(sunlit_values.get(oid, 0)))
           if val == 0:
               continue
           chosen.add(oid)
           acc += val
       return chosen


   def _get_available_gs(self, sat: "Satellite") -> Tuple[Link | None, int]:
       dl_links = [
           l for l in sat.connections if l.status and getattr(l.dst, "type", None) == "ground_station"
       ]
       if not dl_links:
           return None, self.clock.current_slot


       best = min(dl_links, key=self._gs_available_slot)
       return best, self._gs_available_slot(best)


   def _gs_available_slot(self, dl: Link) -> int:
       if not dl.processes:
           return self.clock.current_slot


       remaining = [p.time_cost() for p in dl.processes if p.status and p.time_cost() is not None]
       if not remaining:
           return self.clock.current_slot
       return self.clock.current_slot + min(remaining)


   def _query_energy(self, sat: "Satellite") -> float:
       # 获取基础属性
       battery = sat.battery_percent / 100 * sat.BATTERY_CAPACITY # Wh
       p_solar = sat.power_of_solar_panel # W
       p_compute = sat.power_of_computing # W
      
       # 为了简化，你可以只预估纯充电能力，或者更严谨一点：
       _, cyc_slots = sat.get_orbital_cycle()
       cyc_slots = max(int(cyc_slots or 0), 1)
      
       # 未来一个周期的总日照 slot 数
       sun_slots = self._sunlit_slots_for_sat(sat, self.clock.current_slot, cyc_slots)
      
       # 预估未来能量收入 (功率 * 日照时间)
       expected_income = p_solar * sun_slots * self.clock.SLOT
      
       # 3. 统计当前负载的预期能耗 (债务支出)
       # 遍历所有分配给该卫星且尚未完成的任务
       current_load_slots = 0
       for m in self.world.missions:
           # 只有已经在该卫星上排队（COMPUTING阶段）或确定要发往该卫星的任务才计入
           if m.position.addr == sat.addr\
              and m.status not in {MissionStatus.COMPLETED, MissionStatus.FAILED}:
               current_load_slots += self._task_processing_slots(sat, m)
      
       energy_expense = p_compute * current_load_slots * self.clock.SLOT
      
       # 4. 最终评估结果：预期剩余能量
       return battery + expected_income - energy_expense

