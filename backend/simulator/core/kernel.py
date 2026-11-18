"""The same observe → decide → transition → commit loop for every strategy."""
from copy import deepcopy
from simulator.core.staging import fork_environment
from simulator.core.time_step import step_context
from simulator.policies.base import DecisionPolicy
from simulator.policies.view import PlanningView


class SimulationKernel:
    def advance(self, session):
        candidate = fork_environment(session.environment)
        policy = deepcopy(session.policy)
        context = step_context(candidate)
        before = session.snapshot()
        policy_input = before if session.custom_policy else PlanningView.from_simulator(candidate)
        actions = policy.decide(policy_input, context)
        candidate.transition(actions, context)
        evaluate = getattr(policy, "evaluate", None)
        if evaluate is not None:
            reward = evaluate(before, candidate, actions, context)
            candidate.info = candidate.info.model_copy(update={"reward": reward})
        state = session.collect_snapshot(candidate, candidate.info)
        state.model_dump_json()
        session.environment = candidate
        session.policy = policy
        session.info = state.info
        session.is_completed = candidate.is_completed
        session._state = state
        return state.model_copy(deep=True)
