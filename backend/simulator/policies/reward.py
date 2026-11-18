"""PPO's objective/shaping observes the shared simulator's transition."""
from simulator.config import (COMP_PENALTY, TRAN_PENALTY, LAYER_COMPLETION_REWARD,
    INDIVIDUAL_COMPLETION_REWARD, OVERTIME_PENALTY, ALL_TASK_COMPLETION_REWARD, ENERGY_DROWN_PENALTY)
from simulator.env.core.formulation import compute_delay_penalty, compute_energy_penalty, reward_function
from simulator.env.core.constraints import any_satellite_depleted


def transition_reward(before, simulator, actions, context, selection_reward=0.0, lamda=0.57):
    tasks = {task.id: task for task in simulator.task_manager.tasks}
    active = [tasks[task.id] for task in before.tasks if not task.is_done and task.t_start <= context.frame_counter]
    previous = {task.id: task for task in before.tasks}
    nodes = {node.id: node for node in simulator.sat}
    reward = selection_reward
    links = {(link.src, link.dst): link for link in before.links}
    for action in actions.transfer:
        link = links.get((action.src, action.dst)) or links.get((action.dst, action.src))
        if link is not None and link.rate > 0:
            reward += TRAN_PENALTY
    for action in actions.compute:
        if nodes[action.node_id].is_processing:
            reward += COMP_PENALTY
            task = tasks[action.task_id]
            if task.layer_id > previous[task.id].layer_id:
                reward += LAYER_COMPLETION_REWARD
                if task.is_done:
                    reward += INDIVIDUAL_COMPLETION_REWARD
                    if task.t_end > task.ddl:
                        reward += OVERTIME_PENALTY
    if active:
        reward += reward_function(lamda, compute_delay_penalty(context.dt_s, active),
                                  compute_energy_penalty(context.dt_s, simulator.sat), scale=10.0)
    if tasks and all(task.is_done for task in tasks.values()):
        reward += ALL_TASK_COMPLETION_REWARD
    elif any_satellite_depleted(simulator.sat):
        reward += ENERGY_DROWN_PENALTY
    return float(reward)
