"""Select a scheduling strategy; the simulator is never selected here."""
from simulator.core.actions import SchedulingActions


class IdlePolicy:
    def decide(self, view, context):
        return SchedulingActions()


def create_policy(name, project):
    if name == "geometry":
        return IdlePolicy()
    if name == "ophanim":
        from simulator.policies.ophanim import OphanimPolicy
        return OphanimPolicy()
    if name == "l2d2":
        from simulator.policies.l2d2 import L2D2Policy
        return L2D2Policy()
    if name == "phoenix":
        from simulator.policies.phoenix import PhoenixPolicy
        return PhoenixPolicy()
    if name == "mhspo":
        from simulator.policies.mhspo import MHSPOPolicy
        return MHSPOPolicy()
    if name == "ppo":
        from simulator.policies.ppo import PPOPolicy
        return PPOPolicy(project)
    raise ValueError("Unknown algorithm")
