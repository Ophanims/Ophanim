"""Original Ophanim scheduling equations observing the single shared simulator."""
from collections import deque
from types import SimpleNamespace
from algorithm.phoenix import PhoenixAlgorithm
from simulator.core.actions import ComputeAction, SchedulingActions, TransferAction
from simulator.models.realtime_ephemeris import TS
from simulator.policies.commands import collect_actions
from simulator.policies.ophanim_view import observe_world


class OphanimPolicy:
    def __init__(self):
        self.origins = {}

    def decide(self, view, context):
        world = observe_world(view, self.origins)
        clock = SimpleNamespace(current_slot=view.frame_counter, current_datetime=context.time,
                                current_time=TS.utc(context.time), SLOT=view.slot_in_num)
        planner = PhoenixAlgorithm(world, clock)
        pending = collect_actions(view, view.trans_reqs)
        computations, transfers = list(pending.compute), list(pending.transfer)
        reserved = {action.task_id for action in [*computations, *transfers]}
        occupied = {action.node_id for action in computations}
        active = {task.id for task in view.task_manager.get_tasks_at(view.frame_counter)}
        stations = {station.id for station in view.gs}
        for satellite in world.satellites:
            observation = planner.observe(satellite)
            observation["pending_tasks"] = [task for task in observation["pending_tasks"]
                                              if task.id in active and task.id not in reserved]
            for action in planner.decide(satellite, observation):
                task_id, destination = action["task_id"], action["dst"]
                if task_id in reserved:
                    continue
                if destination == satellite.id:
                    if destination in occupied:
                        continue
                    computations.append(ComputeAction(task_id, destination))
                    occupied.add(destination)
                elif destination in stations:
                    transfers.append(TransferAction(task_id, satellite.id, destination, "sgl"))
                else:
                    next_hop = self._next_hop(view, satellite.id, destination)
                    if next_hop is None:
                        continue
                    transfers.append(TransferAction(task_id, satellite.id, next_hop, "isl"))
                reserved.add(task_id)
        return SchedulingActions(tuple(computations), tuple(transfers))

    @staticmethod
    def _next_hop(view, source, destination):
        frontier, seen = deque([(source, None)]), {source}
        while frontier:
            current, first_hop = frontier.popleft()
            if current == destination:
                return first_hop
            for link in view.net._all_links:
                if link.type != "ISL" or current not in {link.src, link.dst}:
                    continue
                neighbor = link.dst if link.src == current else link.src
                if neighbor not in seen:
                    seen.add(neighbor)
                    frontier.append((neighbor, first_hop or neighbor))
        return None
