from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
	from entity.sat import Satellite


class Algorithm(ABC):
	"""卫星算法抽象模板：感知 -> 决策 -> 执行。"""

	@abstractmethod
	def observe(self, satellite: "Satellite") -> Dict[str, Any]:
		"""感知阶段：从卫星和环境读取状态。"""

	@abstractmethod
	def decide(self, satellite: "Satellite", state: Dict[str, Any]) -> Dict[str, Any]:
		"""决策阶段：根据状态产出动作。"""

	@abstractmethod
	def act(self, satellite: "Satellite", action: Dict[str, Any]) -> None:
		"""执行阶段：将动作作用到卫星实体。"""