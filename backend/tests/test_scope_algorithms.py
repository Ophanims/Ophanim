"""Optional algorithm checks use this repository's dependencies and checkpoints."""
import importlib.util
import unittest

from simulator.defaults import default_project
from simulator.core.session import SimulationSession
from simulator.services.project_service import detect_update
from simulator.settings import SIMULATION_MODEL_DIR

HAS_ML = importlib.util.find_spec("sb3_contrib") is not None


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
    def test_ppo_environment_accepts_seed_and_steps(self):
        from simulator.env.gym_adapter import SimulationGymAdapter
        environment = SimulationGymAdapter(self.project())
        try:
            observation, _ = environment.reset(seed=13)
            self.assertTrue(environment.observation_space.contains(observation))
            initial_tasks = [task.model_dump() for task in environment.simulator.task_manager.tasks]
            for _ in range(3):
                mask = environment.action_masks()
                action = next(index for index, allowed in enumerate(mask) if allowed)
                observation, reward, terminated, truncated, info = environment.step(action)
                self.assertTrue(environment.observation_space.contains(observation))
            environment.reset(seed=13)
            self.assertEqual(initial_tasks, [task.model_dump() for task in environment.simulator.task_manager.tasks])
        finally:
            environment.close()

    @unittest.skipUnless(HAS_ML and (SIMULATION_MODEL_DIR / "final_ppo_leoenv.zip").exists(), "optional PPO checkpoint unavailable")
    def test_imported_ppo_checkpoint_predicts_multiple_steps(self):
        from simulator.services.policy_loader import load_model_and_normalizer
        model, _ = load_model_and_normalizer()
        number_of_planes, number_of_sat_per_planes = model.observation_space.spaces["energy"].shape
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
