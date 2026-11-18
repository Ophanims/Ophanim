"""Load PPO tensors/normalization without an environment framework."""
from simulator.settings import SIMULATION_MODEL_DIR

MODEL_PATH = str(SIMULATION_MODEL_DIR / "final_ppo_leoenv")


def load_model_and_normalizer(model_path: str = MODEL_PATH):
    from simulator.learning.checkpoint import load_checkpoint
    return load_checkpoint(model_path)
