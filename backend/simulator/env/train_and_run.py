from simulator.services.model_paths import create_training_path, publish_checkpoint
from simulator.settings import SIMULATION_MODEL_DIR
from simulator.env.training_reports import _plot_combined_curve, _plot_policy_entropy, _plot_action_distribution, _plot_learning_curve, _compute_score_from_logs

from simulator.schemas.project import Project
from simulator.env.ppo.ppo_env import PPOEnv
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.callbacks import BaseCallback
import os
import argparse
from typing import List

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from simulator.env.ppo.features import SetTaskFeaturesExtractor

from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker

from simulator.env.baselines.auto_testing import AutoTester


# def make_env(input: Project, seed: int = 0, log_dir: str = LOG_DIR):
#     def _init():
#         env = PPOEnv(input)
#         try:
#             env.reset(seed=seed)
#         except TypeError:
#             try:
#                 env.seed(seed)
#             except Exception:
#                 pass
#         # Monitor the base env; no action mask wrapper
#         mon = Monitor(env)
#         return mon

#     return _init

LOG_DIR = str(SIMULATION_MODEL_DIR / "ppo_logs")


def make_env(input: Project, seed: int = 0, log_dir: str = LOG_DIR):
    """Create a single PPOEnv wrapped with action masking and Monitor logging."""

    def _init():
        env = PPOEnv(input)
        env.reset(seed=seed)
        # Use canonical action_masks() API from PPOEnv for MaskablePPO
        env = ActionMasker(env, lambda e: e.action_masks())

        # Log per-episode reward/length for convergence curves
        os.makedirs(log_dir, exist_ok=True)
        monitor_file = os.path.join(log_dir, f"env_{seed}.monitor.csv")
        env_mon = Monitor(env, filename=monitor_file)
        return env_mon

    return _init

def make_env_with_lamda(input: Project, lamda: float, seed: int = 0, log_dir: str | None = None):
    """Create a single PPOEnv for a given lamda, with action masking and Monitor logging.

    ``log_dir`` can be used to separate logs for different lamda values.
    """

    def _init():
        env = PPOEnv(input)
        env.lamda = lamda
        print(f"Environment lamda set to: {env.lamda}")
        env.reset(seed=seed)
        # Use canonical action_masks() API from PPOEnv for MaskablePPO
        env_masked = ActionMasker(env, lambda e: e.action_masks())

        # Log per-episode reward/length for convergence curves
        target_log_dir = log_dir
        os.makedirs(target_log_dir, exist_ok=True)
        monitor_file = os.path.join(target_log_dir, f"env_{seed}.monitor.csv")
        env_mon = Monitor(env_masked, filename=monitor_file)
        return env_mon

    return _init


class TrainingMetricsCallback(BaseCallback):
    """Collects lightweight training statistics for plotting.

    - Approximate policy entropy over a sliding window of actions (Shannon entropy
      of empirical action frequencies), vs. environment steps.
    - Action distribution snapshots at a few training progress checkpoints.
    """

    def __init__(self, total_timesteps: int, window_size: int = 2048, verbose: int = 0):
        super().__init__(verbose)
        self.total_timesteps = int(total_timesteps)
        self.window_size = int(window_size)

        self.action_dim: int | None = None
        self.total_steps: int = 0
        self.actions_window: List[int] = []
        self.all_actions: List[int] = []

        # For entropy curve
        self.entropy_steps: List[int] = []
        self.entropy_values: List[float] = []

        # For action distribution evolution
        self.checkpoints: np.ndarray | None = None
        self.next_checkpoint_idx: int = 0
        self.action_dist_steps: List[int] = []
        self.action_dist_probs: List[np.ndarray] = []

    def _on_training_start(self) -> bool:
        # Only handle discrete action spaces
        if not hasattr(self.model, "action_space") or not hasattr(self.model.action_space, "n"):
            if self.verbose:
                print("[TrainingMetricsCallback] Non-discrete action space; metrics disabled.")
            return True

        self.action_dim = int(self.model.action_space.n)
        # Define 5 checkpoints from 0% to 100% timesteps
        self.checkpoints = np.linspace(0, self.total_timesteps, num=5, dtype=int)
        self.next_checkpoint_idx = 0
        return True

    def _on_step(self) -> bool:
        if self.action_dim is None:
            return True

        actions = self.locals.get("actions")
        if actions is None:
            return True

        actions = np.asarray(actions).reshape(-1)
        if actions.size == 0:
            return True

        self.total_steps += int(actions.size)
        self.actions_window.extend(actions.astype(int).tolist())
        self.all_actions.extend(actions.astype(int).tolist())

        # Update entropy curve when window is filled
        if len(self.actions_window) >= self.window_size:
            counts = np.bincount(self.actions_window, minlength=self.action_dim)
            total = counts.sum()
            if total > 0:
                probs = counts / total
                entropy = float(-(probs * np.log(probs + 1e-12)).sum())
                self.entropy_steps.append(self.total_steps)
                self.entropy_values.append(entropy)
            self.actions_window.clear()

        # Record action distribution snapshots at checkpoints
        if self.checkpoints is not None:
            while self.next_checkpoint_idx < len(self.checkpoints) and self.total_steps >= int(
                self.checkpoints[self.next_checkpoint_idx]
            ):
                step_val = int(self.checkpoints[self.next_checkpoint_idx])
                counts_all = np.bincount(self.all_actions, minlength=self.action_dim)
                total_all = counts_all.sum()
                if total_all > 0:
                    probs_all = counts_all / total_all
                    self.action_dist_steps.append(step_val)
                    self.action_dist_probs.append(probs_all)
                self.next_checkpoint_idx += 1

        return True

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os













def train_model(input: Project):
    # Configuration constants (use these instead of CLI)
    TENSORBOARD_LOG_DIR = str(SIMULATION_MODEL_DIR / "tensorboard")
    MODEL_PATH = create_training_path(input.project_id)
    LOG_DIR = os.path.join(os.path.dirname(MODEL_PATH), "ppo_logs")
    TIMESTEPS = 5000000
    SEEDS = [input.seed + offset for offset in (0, 1, 2, 4)]

    model_dir = os.path.dirname(MODEL_PATH) or "."
    os.makedirs(model_dir, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

    # pass the provided `input` into each env factory
    env_fns = [make_env(input, seed=i, log_dir=LOG_DIR) for i in SEEDS]
    venv = DummyVecEnv(env_fns)

    # Wrap VecNormalize for numeric keys
    venv = VecNormalize(
        venv,
        norm_obs=True,
        norm_reward=True,
        clip_obs=10.0,
        # only normalize fixed-shape fields
        norm_obs_keys=["energy", "sunlight", "comm", "queue", "task_stats"],
    )

    # policy kwargs: slightly larger nets for stability
    policy_kwargs = {
        "net_arch": {"pi": [256, 256], "vf": [256, 256]},
        "features_extractor_class": SetTaskFeaturesExtractor,
        "features_extractor_kwargs": {"embed_dim": 256, "phi_hidden": 128, "rho_hidden": 256},
    }

    # Use MaskablePPO with action masking
    model = MaskablePPO(
        "MultiInputPolicy",
        env=venv,
        verbose=1,

        tensorboard_log=TENSORBOARD_LOG_DIR,

        learning_rate=3e-4,
        n_steps=2048,
        batch_size=1024,
        n_epochs=10,

        gamma=0.99,
        clip_range=0.25,
        target_kl=0.03,
        ent_coef=0.01,
        vf_coef=0.5,
        max_grad_norm=0.5,
        policy_kwargs=policy_kwargs,
        # MaskablePPO does not support use_sde parameter
    )

    # Collect training metrics via callback
    metrics_cb = TrainingMetricsCallback(total_timesteps=TIMESTEPS, window_size=4096)

    model.learn(total_timesteps=TIMESTEPS, callback=metrics_cb)
    model.save(MODEL_PATH)

    venv.save(MODEL_PATH + '.vecnormalize')
    publish_checkpoint(input.project_id, MODEL_PATH)
    venv.close()

    # ---------- Plot training diagnostics ----------
    _plot_policy_entropy(metrics_cb, model_dir)
    _plot_action_distribution(metrics_cb, model_dir)
    _plot_learning_curve(LOG_DIR, model_dir)
    _plot_combined_curve(metrics_cb, model_dir)

    tester = AutoTester(input)
    tester.run()

def train_model_lamda(input: Project):
    # Configuration constants (use these instead of CLI)
    # lamdas = [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9]
    # lamdas = [0.1,0.3,0.5,0.7,0.9]
    lamdas = [0.9]
    # lamdas = [0.1,0.5,0.9]
    # MODEL_PATH = "ai_model/ppo_leoenv"
    TIMESTEPS = 500000
    SEEDS = [0, 1, 2]
    TENSORBOARD_LOG_DIR = str(SIMULATION_MODEL_DIR / "tensorboard")


    for lamda in lamdas:
        print(f"Starting training model with lamda={lamda}")
        MODEL_PATH = f"{SIMULATION_MODEL_DIR}/PPO/lamda_comparison/lamda_{lamda}/ppo_leoenv"

        model_dir = os.path.dirname(MODEL_PATH) or "."
        os.makedirs(model_dir, exist_ok=True)
        # use a separate log dir for each lamda so that scores do not mix
        lamda_log_dir = os.path.join(LOG_DIR, f"lamda_{lamda}")
        os.makedirs(lamda_log_dir, exist_ok=True)

        # pass the provided `input` into each env factory
        env_fns = [make_env_with_lamda(input, lamda, seed=i, log_dir=lamda_log_dir) for i in SEEDS]
        venv = DummyVecEnv(env_fns)

        # Wrap VecNormalize for numeric keys
        venv = VecNormalize(
            venv,
            norm_obs=True,
            norm_reward=True,
            clip_obs=10.0,
            # only normalize fixed-shape fields
            norm_obs_keys=["energy", "sunlight", "comm", "queue", "task_stats"],
        )

        # policy kwargs: slightly larger nets for stability
        policy_kwargs = {
            "net_arch": {"pi": [256, 256], "vf": [256, 256]},
            "features_extractor_class": SetTaskFeaturesExtractor,
            "features_extractor_kwargs": {"embed_dim": 256, "phi_hidden": 128, "rho_hidden": 256},
        }

        # Use MaskablePPO with action masking
        model = MaskablePPO(
            "MultiInputPolicy",
            env=venv,
            verbose=1,

            tensorboard_log=TENSORBOARD_LOG_DIR,

            learning_rate=3e-4,
            n_steps=2048,
            batch_size=1024,
            n_epochs=10,

            gamma=0.99,
            clip_range=0.25,
            target_kl=0.03,
            ent_coef=0.01,
            vf_coef=0.5,
            max_grad_norm=0.5,
            policy_kwargs=policy_kwargs,
            # MaskablePPO does not support use_sde parameter
        )

        # Collect training metrics via callback
        metrics_cb = TrainingMetricsCallback(total_timesteps=TIMESTEPS, window_size=4096)

        model.learn(total_timesteps=TIMESTEPS, callback=metrics_cb)
        model.save(MODEL_PATH)

        try:
            venv.save(MODEL_PATH + '.vecnormalize')
        except (OSError, ValueError) as exc:
            raise RuntimeError("Failed to save the training normalizer") from exc

        # ---------- Plot training diagnostics ----------
        _plot_policy_entropy(metrics_cb, model_dir)
        _plot_action_distribution(metrics_cb, model_dir)
        _plot_learning_curve(lamda_log_dir, model_dir)
        _plot_combined_curve(metrics_cb, model_dir)

    # ---------- Run Auto-Tester after all lamda models trained ----------
    print("Starting Auto-Testing after training all lamda models")
    # tester = AutoTester(input)
    # tester.run()


if __name__ == '__main__':
    raise SystemExit("Use the managed training API with a validated Project")
