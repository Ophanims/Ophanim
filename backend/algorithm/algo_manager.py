from __future__ import annotations

from typing import Dict, List, Type

from algorithm.algo import Algorithm
from algorithm.default import DefaultAlgorithm


class AlgorithmManager:
    """管理算法注册、查询和实例化。"""

    def __init__(self) -> None:
        self._registry: Dict[str, Type[Algorithm]] = {}

    def register(self, name: str, algo_cls: Type[Algorithm], overwrite: bool = False) -> None:
        if not issubclass(algo_cls, Algorithm):
            raise TypeError("algo_cls must inherit from Algorithm")

        key = name.strip().lower()
        if not key:
            raise ValueError("Algorithm name cannot be empty")

        if not overwrite and key in self._registry:
            raise ValueError(f"Algorithm '{key}' already exists")

        self._registry[key] = algo_cls

    def unregister(self, name: str) -> None:
        key = name.strip().lower()
        self._registry.pop(key, None)

    def list_algorithms(self) -> List[str]:
        return sorted(self._registry.keys())

    def has_algorithm(self, name: str) -> bool:
        return name.strip().lower() in self._registry

    def get_algorithm_class(self, name: str) -> Type[Algorithm]:
        key = name.strip().lower()
        if key not in self._registry:
            available = ", ".join(self.list_algorithms()) or "<none>"
            raise KeyError(f"Unknown algorithm '{name}'. Available: {available}")
        return self._registry[key]

    def create(self, name: str = "default") -> Algorithm:
        algo_cls = self.get_algorithm_class(name)
        return algo_cls()


ALGO_MANAGER = AlgorithmManager()
ALGO_MANAGER.register("default", DefaultAlgorithm)
