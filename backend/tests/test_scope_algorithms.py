"""Optional algorithm checks use this repository's dependencies and checkpoints."""
import importlib.util
import unittest

from simulator.defaults import default_project
from simulator.core.session import SimulationSession
from simulator.services.project_service import detect_update
from simulator.settings import SIMULATION_MODEL_DIR

HAS_ML = importlib.util.find_spec("torch") is not None


class BaselineTests(unittest.TestCase):
    def project(self):
        project = default_project()
        project.project_id = "algorithm_test"
        project.seed = 31
        project.constellation.number_of_planes = 2
        project.constellation.number_of_sat_per_planes = 3
        project.experiment.end_time = "2025-12-01T00:02:00+00:00"
        return detect_update(project)

    def test_baselines_repeat_seeded_state_and_step(self):
        for algorithm in ["l2d2", "phoenix", "mhspo"]:
            with self.subTest(algorithm=algorithm):
                first = SimulationSession(self.project(), algorithm)
                second = SimulationSession(self.project(), algorithm)
                try:
                    self.assertEqual(first.snapshot().serialize(), second.snapshot().serialize())
                    for _ in range(3):
                        self.assertEqual(first.step().serialize(), second.step().serialize())
                finally:
                    first.close()
                    second.close()

    @unittest.skipUnless(HAS_ML, "optional ML dependencies not installed")
    def test_native_policy_observations_accept_seed_and_steps(self):
        from simulator.core.simulation import Simulation
        from simulator.policies.discrete_scheduler import DiscreteScheduler
        from simulator.policies.view import PlanningView
        from simulator.env.core.observation import observation_shapes, validate_observation
        simulator = Simulation(self.project())
        self.addCleanup(simulator.close)
        simulator.reset(seed=13)
        initial_tasks = [task.model_dump() for task in simulator.task_manager.tasks]
        shapes = observation_shapes(o=3, p=2)
        for _ in range(3):
            scheduler = DiscreteScheduler()
            scheduler.begin(PlanningView.from_simulator(simulator))
            validate_observation(scheduler.observation(), shapes)
            while not scheduler.finished:
                scheduler.submit(0)
            simulator.step(scheduler.actions())
        simulator.reset(seed=13)
        self.assertEqual(initial_tasks, [task.model_dump() for task in simulator.task_manager.tasks])

    @unittest.skipUnless(HAS_ML and (SIMULATION_MODEL_DIR / "final_ppo_leoenv.zip").exists(), "optional PPO checkpoint unavailable")
    def test_imported_ppo_checkpoint_predicts_multiple_steps(self):
        from simulator.services.policy_loader import load_model_and_normalizer
        model, _ = load_model_and_normalizer()
        number_of_planes, number_of_sat_per_planes = model.observation_shapes["energy"]
        project = self.project()
        project.constellation.number_of_planes = number_of_planes
        project.constellation.number_of_sat_per_planes = number_of_sat_per_planes
        session = SimulationSession(detect_update(project), "ppo")
        try:
            for _ in range(3):
                state = session.step()
                self.assertEqual(number_of_planes * number_of_sat_per_planes, len(state.satellites))
        finally:
            session.close()


if __name__ == "__main__":
    unittest.main()
