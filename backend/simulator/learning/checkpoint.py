"""Native tensor checkpoints and read-only compatibility for existing weights."""
import io
import json
import zipfile
from pathlib import Path
import torch
from simulator.learning.network import ActorCritic
from simulator.learning.normalization import Normalizer


def save_checkpoint(model, normalizer, model_path, training=None):
    path = Path(model_path + ".zip")
    path.parent.mkdir(parents=True, exist_ok=True)
    metadata = {"schema_version": 1, "planes": model.planes, "orders": model.orders,
                "hidden": model.hidden, "embed_dim": model.embed_dim, "training": training or {}}
    buffer = io.BytesIO()
    torch.save(model.state_dict(), buffer)
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("metadata.json", json.dumps(metadata, allow_nan=False))
        archive.writestr("policy.pth", buffer.getvalue())
    normalizer.save(model_path + ".normalizer.json")


def load_checkpoint(model_path):
    path = Path(model_path + ".zip")
    if not path.exists():
        raise FileNotFoundError("PPO checkpoint is unavailable; import the SCOPE models or train a model")
    with zipfile.ZipFile(path) as archive:
        state = torch.load(io.BytesIO(archive.read("policy.pth")), map_location="cpu", weights_only=True)
        if "metadata.json" in archive.namelist():
            metadata = json.loads(archive.read("metadata.json"))
            if metadata["schema_version"] != 1:
                raise ValueError("Unsupported PPO checkpoint version")
            model = ActorCritic(metadata["planes"], metadata["orders"], metadata["hidden"], metadata["embed_dim"])
        else:
            from simulator.learning.legacy_checkpoint import legacy_shapes
            shapes = legacy_shapes(json.loads(archive.read("data")))
            model = ActorCritic(*shapes["energy"], hidden=state["features_extractor.net.0.weight"].shape[0],
                                embed_dim=state["features_extractor.net.2.weight"].shape[0])
            state = _convert_legacy_weights(state)
        model.load_state_dict(state, strict=True)
        model.eval()
    native_normalizer = Path(model_path + ".normalizer.json")
    legacy_path = Path(model_path + ".vecnormalize")
    if native_normalizer.exists():
        normalizer = Normalizer.load(native_normalizer)
    elif legacy_path.exists():
        from simulator.learning.legacy_checkpoint import legacy_normalizer
        normalizer = legacy_normalizer(legacy_path)
    else:
        normalizer = None
    return model, normalizer


def _convert_legacy_weights(state):
    prefixes = {"features_extractor.net.": "features.", "mlp_extractor.policy_net.": "policy_net.",
                "mlp_extractor.value_net.": "value_net.", "value_net.": "value_head.", "action_net.": "action_net."}
    for prefix in ("pi_features_extractor.net.", "vf_features_extractor.net."):
        for key, value in state.items():
            if key.startswith(prefix) and not torch.equal(value, state[key.replace(prefix, "features_extractor.net.")]):
                raise ValueError("Checkpoint uses separate feature networks; unsupported architecture")
    converted = {}
    for key, value in state.items():
        for old, new in prefixes.items():
            if key.startswith(old):
                converted[new + key[len(old):]] = value
                break
    return converted
