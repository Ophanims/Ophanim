"""Native PPO math, checkpoint compatibility, and direct-simulator training."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import numpy as np

HAS_TORCH = importlib.util.find_spec("torch") is not None


@unittest.skipUnless(HAS_TORCH, "optional PyTorch dependency unavailable")
class NativePPOTests(unittest.TestCase):
    def project(self):
        from simulator.defaults import default_project
        from simulator.services.project_service import detect_update
        project = default_project()
        project.project_id = "native_training_test"
        project.seed = 31
        project.constellation.number_of_planes = 2
        project.constellation.number_of_sat_per_planes = 3
        project.experiment.time_slot = 0.5
        project.experiment.end_time = "2025-12-01T00:00:01.300000+00:00"
        return detect_update(project)

    def test_gae_bootstraps_but_does_not_cross_episode_boundaries(self):
        from simulator.learning.rollout import compute_gae
        advantages, returns = compute_gae([1, 2, 5], [0, 0, 0], [False, True, False], 7, 1, 1)
        np.testing.assert_allclose(advantages, [3, 2, 12])
        np.testing.assert_allclose(returns, [3, 2, 12])

    def test_clipped_objective_value_loss_entropy_and_kl(self):
        import torch
        from simulator.learning.ppo import ppo_loss, PPOConfig
        result = ppo_loss(torch.log(torch.tensor([2.0, 0.5])), torch.tensor([0.0, 2.0]),
            torch.tensor([0.2, 0.4]), torch.zeros(2), torch.tensor([1.0, -1.0]), torch.ones(2), PPOConfig())
        loss, policy, value, entropy, kl = [float(item) for item in result]
        self.assertAlmostEqual(-0.25 / np.sqrt(2), policy, places=6)
        self.assertAlmostEqual(1.0, value)
        self.assertAlmostEqual(0.3, entropy)
        self.assertAlmostEqual(0.25, kl)
        self.assertAlmostEqual(policy - 0.003 + 0.5, loss, places=6)

    def test_masked_actions_have_zero_probability_and_finite_entropy(self):
        import torch
        from simulator.learning.network import ActorCritic
        model = ActorCritic(2, 3)
        observation = {key: np.zeros(shape, np.float32) for key, shape in model.observation_shapes.items()}
        features = torch.from_numpy(model.vectorize(observation))[None]
        mask = np.asarray([False, False, False, False, False, True])
        distribution, _, _ = model.distribution(features, mask)
        np.testing.assert_array_equal(distribution.probs.detach().numpy(), [[0, 0, 0, 0, 0, 1]])
        self.assertEqual(5, model.choose_action(observation, mask).action)
        _, _, entropy = model.evaluate(features, torch.tensor([5]), mask)
        self.assertEqual(0.0, float(entropy.detach()))
        with self.assertRaises(ValueError):
            model.choose_action(observation, np.zeros(6, bool))

    def test_native_checkpoint_and_normalizer_roundtrip(self):
        import torch
        from simulator.learning.network import ActorCritic
        from simulator.learning.normalization import Normalizer
        from simulator.learning.checkpoint import save_checkpoint, load_checkpoint
        model = ActorCritic(2, 3)
        normalizer = Normalizer(model.observation_shapes)
        observation = {key: np.ones(shape, np.float32) for key, shape in model.observation_shapes.items()}
        normalizer.observe(observation)
        normalizer.reward(2.0, 0, False)
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "policy")
            save_checkpoint(model, normalizer, path)
            restored, stats = load_checkpoint(path)
            for key, value in model.state_dict().items():
                self.assertTrue(torch.equal(value, restored.state_dict()[key]))
            for key, value in normalizer.normalize_obs(observation).items():
                np.testing.assert_array_equal(value, stats.normalize_obs(observation)[key])

    def test_training_updates_weights_from_real_simulator_samples(self):
        import torch
        from simulator.learning.network import ActorCritic
        from simulator.learning.normalization import Normalizer
        from simulator.learning.rollout import RolloutCollector
        from simulator.learning.ppo import PPOConfig, PPOOptimizer
        model = ActorCritic(2, 3)
        before = {key: value.clone() for key, value in model.state_dict().items()}
        collector = RolloutCollector(self.project(), (31, 32))
        self.addCleanup(collector.close)
        rollout = collector.collect(model, Normalizer(model.observation_shapes), min_samples=8)
        self.assertGreaterEqual(len(rollout), 8)
        self.assertTrue(np.isfinite(rollout.advantages).all())
        self.assertTrue(rollout.masks[np.arange(len(rollout)), rollout.actions].all())
        update = PPOOptimizer(model, PPOConfig(n_steps=4, batch_size=4, n_epochs=2)).update(rollout)
        self.assertTrue(all(np.isfinite(value) for value in update.values()))
        self.assertTrue(any(not torch.equal(before[key], value) for key, value in model.state_dict().items()))

    def test_managed_training_entry_saves_publishes_and_loads_a_native_run(self):
        from simulator.env.train_and_run import train_model
        from simulator.learning.ppo import PPOConfig
        from simulator.services.model_paths import model_path_for_project
        from simulator.services.policy_loader import load_model_and_normalizer
        with tempfile.TemporaryDirectory() as directory, \
             patch("simulator.services.model_paths.SIMULATION_MODEL_DIR", Path(directory)):
            path = train_model(self.project(), total_timesteps=8,
                config=PPOConfig(n_steps=4, batch_size=4, n_epochs=1), seeds=(31,), evaluate=False)
            self.assertEqual(path, model_path_for_project(self.project().project_id))
            model, normalizer = load_model_and_normalizer(path)
            self.assertEqual((2, 3), model.observation_shapes["energy"])
            self.assertIsNotNone(normalizer)
            root = Path(path).parent
            for filename in ("training.json", "training.csv", "episodes.csv", "ppo_training.png"):
                self.assertTrue((root / filename).is_file(), filename)
            pointer = json.loads((root.parent.parent / "latest.json").read_text())
            self.assertEqual(root.name, pointer["run_id"])

    def test_runtime_loading_and_training_do_not_import_environment_frameworks(self):
        # A fresh process rejects even a transitive import, so installed legacy
        # packages cannot conceal a remaining runtime dependency.
        code = '''
import importlib.abc, sys
class BlockFrameworks(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'gymnasium', 'gym', 'stable_baselines3', 'sb3_contrib'}:
            raise AssertionError('Unexpected dependency: ' + fullname)
sys.meta_path.insert(0, BlockFrameworks())
from simulator.services.policy_loader import load_model_and_normalizer
from simulator.env.train_and_run import train_model
from simulator.learning.rollout import RolloutCollector
from simulator.learning.ppo import PPOConfig, PPOOptimizer
from simulator.learning.normalization import Normalizer
from simulator.learning.network import ActorCritic
from simulator.learning.checkpoint import save_checkpoint
import tempfile
with tempfile.TemporaryDirectory() as directory:
    fresh = ActorCritic(2, 3)
    path = directory + '/policy'
    save_checkpoint(fresh, Normalizer(fresh.observation_shapes), path)
    load_model_and_normalizer(path)
try:
    load_model_and_normalizer()
except FileNotFoundError:
    pass
from simulator.defaults import default_project
from simulator.services.project_service import detect_update
project = default_project()
project.constellation.number_of_planes = 2
project.constellation.number_of_sat_per_planes = 3
project.experiment.time_slot = 0.5
project.experiment.end_time = '2025-12-01T00:00:01.300000+00:00'
project = detect_update(project)
collector = RolloutCollector(project, (31,))
try:
    fresh = ActorCritic(2, 3)
    rollout = collector.collect(fresh, Normalizer(fresh.observation_shapes), 4)
    PPOOptimizer(fresh, PPOConfig(n_steps=4, batch_size=4, n_epochs=1)).update(rollout)
finally:
    collector.close()
print('No framework dependency')
'''
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
        result = subprocess.run([sys.executable, "-c", code], env=environment,
                                capture_output=True, text=True, timeout=60)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("No framework dependency", result.stdout)


if __name__ == "__main__":
    unittest.main()
