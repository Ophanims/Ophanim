from simulator.core.actions import ComputeAction, SchedulingActions, TransferAction


def collect_actions(environment, transfer_requests) -> SchedulingActions:
    return SchedulingActions(
        compute=tuple(ComputeAction(r["task_id"], r["node"].id)
                      for r in getattr(environment, "comp_reqs", [])),
        transfer=tuple(TransferAction(r["task_id"], r["node"].id, r["dst"], r.get("type", "sgl"), r.get("weight", 1.0))
                       for r in transfer_requests),
    )


def finish_planning(environment, transfer_requests, ages) -> SchedulingActions:
    actions = collect_actions(environment, transfer_requests)
    for task in environment.task_manager.tasks:
        task.t_end = ages[task.id]
    return actions
