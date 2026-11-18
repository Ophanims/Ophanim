"""Algorithm-independent task, link, station and satellite state transition."""
from collections import defaultdict
from simulator.config import LAYER_OUTPUT_DATA_SIZE
from simulator.core.actions import ComputeAction, SchedulingActions, SatelliteAction, StationAction, TaskAction
from simulator.core.time_step import advance_time
from simulator.entities.link_entity import LinkAction, LinkEntity


def execute_actions(environment, actions: SchedulingActions, context):
    if not isinstance(actions, SchedulingActions):
        raise TypeError("Policies must return SchedulingActions")
    tasks = {task.id: task for task in environment.task_manager.tasks}
    nodes = {node.id: node for node in environment.sat}
    stations = {station.id: station for station in environment.gs}
    links = {(link.src, link.dst): link for link in environment.net._all_links}
    node_activity = {node.id: [False, False, False] for node in environment.sat}
    station_activity = set()
    computing_nodes, scheduled_tasks = set(), set()
    for action in (*actions.compute, *actions.transfer):
        task = tasks[action.task_id]
        node_id = action.node_id if isinstance(action, ComputeAction) else action.src
        node = nodes[node_id]
        if task.is_done or task.t_start > context.frame_counter:
            raise ValueError("Cannot schedule a completed or future task")
        if (task.plane_at, task.order_at) != (node.plane, node.order):
            raise ValueError("Action source must own the task")
        if action.task_id in scheduled_tasks:
            raise ValueError("A task may have only one action per slot")
        scheduled_tasks.add(action.task_id)
        if isinstance(action, ComputeAction):
            if node_id in computing_nodes:
                raise ValueError("A satellite may compute only one task per slot")
            computing_nodes.add(node_id)
        elif action.dst not in (nodes if action.kind == "isl" else stations):
            raise ValueError("Unknown transmission destination")

    for task in tasks.values():
        if not task.is_done and task.t_start <= context.frame_counter:
            task.transition(TaskAction("age", elapsed_slots=1), context)

    # Allocate all shares before executing/removing any completed request.
    grouped = defaultdict(list)
    for action in actions.transfer:
        key = tuple(sorted((action.src, action.dst))) if action.kind == "isl" else (action.src, action.dst)
        grouped[key].append(action)
    allocations = {}
    for requests in grouped.values():
        first = requests[0]
        link = links.get((first.src, first.dst)) or links.get((first.dst, first.src))
        if link is None:
            continue  # Retain the request until the link becomes available.
        model = LinkEntity(link)
        model.transition(LinkAction(tuple((r.task_id, r.weight) for r in requests)), context)
        for request in requests:
            budget = model.allocated_bits[request.task_id]
            receiver_weight = sum(r.weight for r in actions.transfer if r.dst == request.dst)
            budget = min(budget, link.rate * context.dt_s * request.weight / receiver_weight)
            allocations[request.task_id] = budget

    remaining_transfers = []
    for action in actions.transfer:
        task, node = tasks[action.task_id], nodes[action.src]
        data_bits = allocations.get(task.id, 0.0)
        if data_bits <= 0 or node.battery_ratio <= 0:
            remaining_transfers.append(action)
            continue
        is_ground = action.kind == "sgl"
        node_activity[node.id][2 if is_ground else 1] = True
        destination = stations[action.dst] if is_ground else nodes[action.dst]
        direction = None
        if is_ground:
            station_activity.add(action.dst)
        else:
            dp, do = destination.plane - node.plane, destination.order - node.order
            direction = 1 if dp == 1 and do == 0 else 2 if dp == -1 and do == 0 else 3 if dp == 0 and do == 1 else 4
        target_bits = LAYER_OUTPUT_DATA_SIZE[task.layer_id]
        task.transition(TaskAction("transfer", data_bits=data_bits, target_bits=target_bits,
            dst_plane=None if is_ground else destination.plane, dst_order=None if is_ground else destination.order,
            to_ground=is_ground, acted=direction), context)
        if task.data_percent > 0:
            remaining_transfers.append(action)
        elif is_ground:
            environment.at_ground += 1
        else:
            environment.task_isl_hops[task.id] = environment.task_isl_hops.get(task.id, 0) + 1

    remaining_compute = []
    for action in actions.compute:
        task, node = tasks[action.task_id], nodes[action.node_id]
        if node.battery_ratio <= 0:
            remaining_compute.append(action)
            continue
        node_activity[node.id][0] = True
        if node.is_charging:
            environment.at_sunlit_sat += 1
        else:
            environment.at_dark_sat += 1
        layer = task.layer_id
        task.transition(TaskAction("compute", nominal_slot_s=environment.slot_in_num, acted=5,
                                   weighted_completion=True), context)
        if task.layer_id == layer:
            remaining_compute.append(action)

    for node_id, activity in node_activity.items():
        nodes[node_id].transition(SatelliteAction(*activity), context)
    advance_time(environment, context)
    # Geometry refresh must not erase the activity during the completed interval.
    for node_id, activity in node_activity.items():
        nodes[node_id].transition(SatelliteAction(*activity, update_energy=False), context)
    for station in environment.gs:
        station.transition(StationAction(on_download=station.id in station_activity), context)
    environment.comp_reqs = [{"task_id": a.task_id, "node": nodes[a.node_id]} for a in remaining_compute]
    environment.trans_reqs = [{"task_id": a.task_id, "node": nodes[a.src], "dst": a.dst, "type": a.kind, "weight": a.weight,
        "selected_link": links.get((a.src, a.dst)) or links.get((a.dst, a.src))} for a in remaining_transfers]

