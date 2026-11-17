"""Explicit optional policy dependency and checkpoint compatibility boundary."""
from pathlib import Path
import torch
from simulator.settings import SIMULATION_MODEL_DIR, SIMULATION_TORCH_THREADS

torch.set_num_threads(SIMULATION_TORCH_THREADS)

MODEL_PATH = str(SIMULATION_MODEL_DIR / "final_ppo_leoenv")


def load_model_and_normalizer(model_path: str = MODEL_PATH):
    from sb3_contrib import MaskablePPO
    from stable_baselines3.common.vec_env import VecNormalize
    from simulator.env.ppo.features import SetTaskFeaturesExtractor
    import pickle
    if not Path(model_path + ".zip").exists():
        raise FileNotFoundError("PPO checkpoint is unavailable; import the SCOPE models or train a model")
    # Historical checkpoints refer to the old module path for this extractor.
    policy_kwargs = {
        "net_arch": {"pi": [256, 256], "vf": [256, 256]},
        "features_extractor_class": SetTaskFeaturesExtractor,
        "features_extractor_kwargs": {"embed_dim": 256, "phi_hidden": 128, "rho_hidden": 256},
    }
    model = MaskablePPO.load(model_path, device="cpu", custom_objects={"policy_kwargs": policy_kwargs})
    normalizer_path = Path(model_path + ".vecnormalize")
    normalizer = None
    if normalizer_path.exists():
        with normalizer_path.open("rb") as stream:
            normalizer = pickle.load(stream)
        normalizer.training = False
        normalizer.norm_reward = False
    return model, normalizer
