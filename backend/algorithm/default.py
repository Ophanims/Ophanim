from typing import Any, Dict, List

from algorithm.algo import Algorithm
from backend.topology.link import Link
from entity.mission import Mission
from backend.topology.node import Node
from entity.sat import Satellite


class DefaultAlgorithm(Algorithm):
	"""默认算法：不改变行为，仅保留三阶段流程结构。"""

	def observe(self, nodes: List[Node], links: List[Link], missions: List[Mission]) -> Dict[str, Any]:
		return {
			"id": satellite.id,
			"battery_level": satellite.battery_level,
			"processor_clock_frequency": satellite.processor_clock_frequency,
			"missions_in_queue": len(satellite.missions),
			"onSUN": satellite.onSUN,
			"position": {
				"x": satellite.x,
				"y": satellite.y,
				"z": satellite.z,
				"lat": satellite.lat,
				"lon": satellite.lon,
				"alt": satellite.alt,
			},
		}

	def decide(self, satellite: "Satellite", state: Dict[str, Any]) -> Dict[str, Any]:
		_ = satellite
		_ = state
		return {}

	def act(self, satellite: "Satellite", action: Dict[str, Any]) -> None:
		# 默认算法不执行任何动作；用户算法可重载并修改卫星状态。
		_ = satellite
		_ = action
