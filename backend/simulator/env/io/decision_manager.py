from typing import Dict, List, Tuple

from simulator.config import DEBUG, MAX_NUM_LAYERS, MAX_NUM_TASKS


class DecisionManager:
    """
    A sparse, dictionary-based decision buffer for actions.
    - pi[(p, o, m)] = int
    - rho[(up, uo, vp, vo, m)] = int

    Layer index `n` has been removed from the decision tensors. If layer
    information is needed by consumers (e.g., for bandwidth weights), they
    should query the StateManager (e.g., sm.get_progress(m)).
    """

    def __init__(self, p_max: int, o_max: int):

        # retained for reference/documentation
        self.P_MAX = p_max
        self.O_MAX = o_max

        # sparse storages (without layer index n)
        self.pi: Dict[Tuple[int, int, int], int] = {}
        self.rho: Dict[Tuple[int, int, int, int, int], int] = {}


    def report(self, step: int) -> Dict[str, dict]:
        alpha_t = self._to_alpha()
        return alpha_t

    def reset(self):
        self.pi.clear()
        self.rho.clear()

    def write_pi(self, p: int, o: int, m: int, value: int):
        # p,o are plane and order indices; m is task id
        key = (p, o, m)
        if value:
            self.pi[key] = 1
        else:
            # remove falsy entries to keep sparse
            self.pi.pop(key, None)

    def write_rho(self, u: Tuple[int, int], v: Tuple[int, int], m: int, value: int):
        # u and v are tuples (plane, order)
        up, uo = u
        vp, vo = v
        key = (up, uo, vp, vo, m)
        if value:
            self.rho[key] = 1
        else:
            self.rho.pop(key, None)
        # if DEBUG:
        #     print(f"[DM] write_rho u={u} v={v} m={m} value={bool(value)}")

    def get_rho(self, u: Tuple[int, int], v: Tuple[int, int], m: int) -> int:
        up, uo = u
        vp, vo = v
        return int(self.rho.get((up, uo, vp, vo, m), 0))

    def get_pi(self, p: int, o: int, m: int) -> int:
        return int(self.pi.get((p, o, m), 0))

    def is_po_occupied(self, p: int, o: int) -> bool:
        # Any active (p,o,*) entry implies occupancy
        for (pp, oo, m), val in self.pi.items():
            if pp == p and oo == o and val:
                return True
        return False

    def get_rho_by_uv(self, u: Tuple[int, int], v: Tuple[int, int]) -> Dict[int, bool]:
        result: Dict[int, bool] = {}
        up, uo = u
        vp, vo = v
        # collect existing (m,n) for this edge
        for (uu, uu_o, vv, vv_o, m), val in self.rho.items():
            if uu == up and uu_o == uo and vv == vp and vv_o == vo:
                result[m] = bool(val)
        # if DEBUG:
        #     true_count = sum(1 for val in result.values() if val)
        #     print(f"[DM] get_rho_by_uv u={u} v={v} tasks={len(result)} true_count={true_count}")
        return result

    def _to_alpha(self) -> Dict[str, dict]:
        # return shallow copies (immutable snapshot) of current sparse tensors
        return {
            "pi": dict(self.pi),
            "rho": dict(self.rho),
        }
