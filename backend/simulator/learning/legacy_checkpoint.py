"""Read numeric legacy checkpoint metadata without importing training frameworks."""
import base64
import io
import pickle
import numpy as np
from simulator.learning.normalization import Normalizer, RunningMoments


class LegacyState:
    def __setstate__(self, state):
        self.__dict__.update(state)


class NumericUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        # Replace these historical containers with inert data, never invoke
        # their constructors, callbacks, wrapper state restoration or imports.
        containers = {("stable_baselines3.common.vec_env.vec_normalize", "VecNormalize"),
            ("stable_baselines3.common.running_mean_std", "RunningMeanStd"),
            ("gymnasium.spaces.dict", "Dict"), ("gymnasium.spaces.box", "Box"),
            ("gymnasium.spaces.discrete", "Discrete")}
        if (module, name) in containers:
            return LegacyState
        allowed = {("numpy", "ndarray"), ("numpy", "dtype"),
            ("numpy.core.multiarray", "_reconstruct"), ("numpy.core.multiarray", "scalar"),
            ("numpy.core.numeric", "_frombuffer"), ("collections", "OrderedDict")}
        if (module, name) in allowed:
            return super().find_class(module, name)
        raise pickle.UnpicklingError(f"Unsupported legacy numeric container: {module}.{name}")


def legacy_shapes(metadata):
    state = NumericUnpickler(io.BytesIO(base64.b64decode(metadata["observation_space"][":serialized:"]))).load()
    return {key: tuple(value._shape) for key, value in state.spaces.items()}


def legacy_normalizer(path):
    with open(path, "rb") as stream:
        state = NumericUnpickler(stream).load()
    result = Normalizer({})
    for key in ("gamma", "epsilon", "clip_obs", "clip_reward", "norm_obs"):
        setattr(result, key, getattr(state, key))
    result.obs_rms = {key: RunningMoments.restore({"mean": value.mean, "var": value.var, "count": value.count})
                      for key, value in state.obs_rms.items()}
    result.ret_rms = RunningMoments.restore({"mean": state.ret_rms.mean, "var": state.ret_rms.var,
                                            "count": state.ret_rms.count})
    return result
