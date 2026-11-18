"""Native PPO training: policy decisions → Simulation.step(actions) → samples."""
import csv
import json
from dataclasses import asdict
from pathlib import Path
import numpy as np
import torch
from simulator.learning.checkpoint import load_checkpoint, save_checkpoint
from simulator.learning.network import ActorCritic
from simulator.learning.normalization import Normalizer
from simulator.learning.ppo import PPOConfig, PPOOptimizer
from simulator.learning.rollout import RolloutCollector
from simulator.schemas.project import Project
from simulator.services.model_paths import create_training_path, publish_checkpoint


def train_model(input: Project, total_timesteps=5_000_000, config=PPOConfig(), seeds=None, lamda=0.57, evaluate=True):
    if total_timesteps < 1:
        raise ValueError("Training timesteps must be positive")
    seeds = tuple(seeds) if seeds is not None else tuple(input.seed + offset for offset in (0, 1, 2, 4))
    model_path = create_training_path(input.project_id)
    directory = Path(model_path).parent
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(input.seed)
        model = ActorCritic(input.constellation.number_of_planes, input.constellation.number_of_sat_per_planes)
    normalizer = Normalizer(model.observation_shapes, gamma=config.gamma)
    optimizer = PPOOptimizer(model, config, seed=input.seed)
    collector = RolloutCollector(input, seeds, lamda)
    fields = ["steps", "loss", "policy_loss", "value_loss", "entropy", "approximate_kl", "mean_reward"]
    fields += [f"action_{index}" for index in range(6)]
    steps, action_counts = 0, np.zeros(6, dtype=np.int64)
    try:
        settings = {**asdict(config), "seeds": seeds, "lamda": lamda,
                    "project": input.serialize(), "requested_timesteps": total_timesteps}
        (directory / "training.json").write_text(json.dumps(settings, allow_nan=False, indent=2))
        with (directory / "training.csv").open("w", newline="") as metrics_file, \
             (directory / "episodes.csv").open("w", newline="") as episodes_file:
            metrics = csv.DictWriter(metrics_file, fieldnames=fields)
            episodes = csv.DictWriter(episodes_file, fieldnames=["steps", "reward", "length", "seed"])
            metrics.writeheader()
            episodes.writeheader()
            while steps < total_timesteps:
                rollout = collector.collect(model, normalizer,
                    min(config.n_steps * len(seeds), total_timesteps - steps), config.gae_lambda)
                update = optimizer.update(rollout)
                steps += len(rollout)
                action_counts += np.bincount(rollout.actions, minlength=6)
                metrics.writerow({"steps": steps, **update, "mean_reward": float(rollout.rewards.mean()),
                    **{f"action_{index}": int(value) for index, value in enumerate(action_counts)}})
                for episode in collector.episodes:
                    episodes.writerow({"steps": steps, **episode})
                collector.episodes.clear()
                metrics_file.flush()
                episodes_file.flush()
                print(f"PPO decisions={steps}/{total_timesteps} loss={update['loss']:.6f}", flush=True)
        save_checkpoint(model, normalizer, model_path, training={**asdict(config), "steps": steps, "seeds": seeds})
        # A published pointer only references a complete, loadable checkpoint.
        load_checkpoint(model_path)
        from simulator.env.training_reports import plot_training_report
        plot_training_report(directory)
        publish_checkpoint(input.project_id, model_path)
    finally:
        collector.close()
    if evaluate:
        from simulator.env.baselines.auto_testing import AutoTester
        AutoTester(input).run()
    return model_path


if __name__ == "__main__":
    raise SystemExit("Use the managed training API with a validated Project")
