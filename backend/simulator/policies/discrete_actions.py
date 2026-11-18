from typing import List
import numpy as np
from simulator.schemas.task import Task


class DiscreteActions:
    def action_masks(self) -> np.ndarray:
        """Return the allowed actions for the current simulator task.

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
        for action in allowed_actions:
            mask[action] = 1
        return mask


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
