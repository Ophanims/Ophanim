"""Policy choice cannot change the environment, seed, clock or transition law."""
import importlib.util
import unittest
from simulator.core.actions import ComputeAction, SchedulingActions
from simulator.core.session import SimulationSession
from simulator.core.simulation import Simulation
from simulator.core.time_step import step_context
from simulator.defaults import default_project
from simulator.policies.view import PlanningView
from simulator.schemas.task import Task
from simulator.services.project_service import detect_update


def shared_project():
    value = default_project()
    value.project_id = "single_environment_test"
    value.seed = 31
    value.constellation.number_of_planes = 2
    value.constellation.number_of_sat_per_planes = 3
    value.experiment.time_slot = 0.5
    value.experiment.end_time = "2025-12-01T00:00:01.300000+00:00"
    return detect_update(value)


class ComputeFirstTask:
    def decide(self, state, context):
        tasks = [task for task in state.tasks if not task.is_done and task.t_start <= state.frame_counter]
        if not tasks:
            return SchedulingActions()
        task = tasks[0]
        node = next(node for node in state.satellites if (node.plane, node.order) == (task.plane_at, task.order_at))
        return SchedulingActions(compute=(ComputeAction(task.id, node.id),))


class SingleEnvironmentTests(unittest.TestCase):
    def session(self, name, **kwargs):
        session = SimulationSession(shared_project(), name, **kwargs)
        self.addCleanup(session.close)
        return session

    def test_all_strategies_start_in_the_exact_same_world(self):
        reference = self.session("geometry").snapshot()
        for name in ("ophanim", "l2d2", "phoenix", "mhspo"):
            with self.subTest(policy=name):
                session = self.session(name)
                self.assertIs(type(session.environment), Simulation)
                self.assertEqual(reference, session.snapshot())
                self.assertEqual(0.5, session.environment.slot_in_num)

    def test_identical_actions_have_identical_results_for_every_algorithm_label(self):
        reference = self.session("geometry", policy=ComputeFirstTask())
        for name in ("ophanim", "l2d2", "phoenix", "mhspo", "ppo"):
            other = self.session(name, policy=ComputeFirstTask())
            expected = []
            # Reset the reference's world independently; policies use no RNG.
            reference.environment.reset()
            reference.is_completed = False
            reference._state = reference.environment.snapshot()
            while not reference.is_completed:
                expected.append(reference.step())
            actual = []
            while not other.is_completed:
                actual.append(other.step())
            self.assertEqual(expected, actual, name)
            self.assertEqual(3, len(actual))

    def test_real_policy_decisions_leave_the_world_unchanged(self):
        for name in ("ophanim", "l2d2", "phoenix", "mhspo"):
            session = self.session(name)
            before = session.environment.snapshot()
            configuration = session.environment.input.serialize()
            actions = session.policy.decide(PlanningView.from_simulator(session.environment),
                                             step_context(session.environment))
            self.assertIsInstance(actions, SchedulingActions)
            self.assertEqual(before, session.environment.snapshot(), name)
            self.assertEqual(configuration, session.environment.input.serialize(), name)
            self.assertFalse(hasattr(session.policy, "time_recorder"))

    def test_simulator_step_rolls_back_on_invalid_joint_actions(self):
        simulator = Simulation(shared_project())
        self.addCleanup(simulator.close)
        before = simulator.snapshot()
        task = next(task for task in before.tasks if task.t_start == 0)
        node = next(node for node in before.satellites if (node.plane, node.order) == (task.plane_at, task.order_at))
        action = ComputeAction(task.id, node.id)
        with self.assertRaisesRegex(ValueError, "one action"):
            simulator.step(SchedulingActions(compute=(action, action)))
        self.assertEqual(before, simulator.snapshot())

    def test_energy_depletion_is_a_shared_environment_terminal_condition(self):
        simulator = Simulation(shared_project())
        self.addCleanup(simulator.close)
        simulator.sat[0].battery = simulator.sat[0].battery_ratio = 0.0
        simulator.sat[0].is_charging = False
        simulator.step()
        self.assertTrue(simulator.is_completed)
        self.assertEqual("satellite_energy_depleted", simulator.info.terminated_reason)

    @unittest.skipUnless(importlib.util.find_spec("sb3_contrib"), "ML dependencies unavailable")
    def test_gym_and_direct_calls_use_the_same_state_transition(self):
        from simulator.env.gym_adapter import SimulationGymAdapter
        adapter = SimulationGymAdapter(shared_project())
        direct = Simulation(shared_project())
        self.addCleanup(adapter.close)
        self.addCleanup(direct.close)
        for simulator in (adapter.simulator, direct):
            simulator.task_manager.tasks = [Task(id=index, plane_at=node.plane, order_at=node.order,
                t_start=0, t_end=0) for index, node in enumerate(simulator.sat[:2])]
            simulator.match_tasks()
        adapter._begin_slot()
        adapter.step(5)
        self.assertEqual(0, adapter.simulator.frame_counter)
        adapter.step(5)
        direct.step(SchedulingActions(compute=tuple(ComputeAction(index, node.id)
            for index, node in enumerate(direct.sat[:2]))))
        self.assertEqual(direct.snapshot(), adapter.simulator.snapshot())

    @unittest.skipUnless(importlib.util.find_spec("sb3_contrib"), "ML dependencies unavailable")
    def test_ppo_initial_state_and_training_adapter_follow_the_shared_configuration(self):
        from simulator.services.policy_loader import load_model_and_normalizer
        model, _ = load_model_and_normalizer()
        project = shared_project()
        planes, orders = model.observation_space.spaces["energy"].shape
        project.constellation.number_of_planes = planes
        project.constellation.number_of_sat_per_planes = orders
        project = detect_update(project)
        ppo = SimulationSession(project, "ppo")
        other = SimulationSession(project, "geometry")
        self.addCleanup(ppo.close)
        self.addCleanup(other.close)
        self.assertEqual(other.snapshot(), ppo.snapshot())
        from simulator.env.gym_adapter import SimulationGymAdapter
        from stable_baselines3.common.env_checker import check_env
        adapter = SimulationGymAdapter(shared_project())
        self.addCleanup(adapter.close)
        check_env(adapter, warn=False)


if __name__ == "__main__":
    unittest.main()
