
import json
from pathlib import Path
from typing import Dict, Tuple, List

import numpy as np
from simulator.env.vars.edge import Edge
from simulator.env.vars.node import Node
from simulator.services.network_service import LinkSnapshot
from simulator.entities.satellite_entity import SatelliteEntity
from simulator.schemas.project import Project

class EntityCol:
    def __init__(self, input: Project):
        self.seed = input.seed
        self.nodes = []
        self.edges = []
        self.nodes_dict: Dict[Tuple[int, int], SatelliteEntity] = {}
        self.edges_dict: Dict[Tuple[Tuple[int, int], Tuple[int, int]], LinkSnapshot] = {}
        self.number_of_sat_per_planes = input.constellation.number_of_sat_per_planes
        self.number_of_planes = input.constellation.number_of_planes

    def reset(self, sats: List[SatelliteEntity], edges: List[LinkSnapshot]):
        self.nodes_dict.clear()
        self.edges_dict.clear()
        self.number_of_sat_per_planes = 0
        self.number_of_planes = 0
        self.load(sats, edges)

    def load(self, sats: List[SatelliteEntity], edges: List[LinkSnapshot]):
        self.nodes = sats
        self.edges = edges
        self._convert()

    def _convert(self):
        index_map = {}
        for n in self.nodes:
            p = n.plane
            o = n.order
            self.nodes_dict[(p, o)] = n
            index_map[n.id] = (p, o)

        for e in self.edges:
            uid = e.src
            vid = e.dst
            if e.src not in index_map or e.dst not in index_map:
                continue
            self.edges_dict[(index_map[uid], index_map[vid])] = e
            self.edges_dict[(index_map[vid], index_map[uid])] = e
        self.number_of_sat_per_planes = max(o for (p, o) in self.nodes_dict.keys()) + 1 if self.nodes_dict else 0
        self.number_of_planes = max(p for (p, o) in self.nodes_dict.keys()) + 1 if self.nodes_dict else 0

    def get_nodes(self) -> List[SatelliteEntity]:
        return list(self.nodes_dict.values())

    def get_edges(self) -> List[LinkSnapshot]:
        return list(self.edges_dict.values())

    def get_node_keys(self) -> List[Tuple[int, int]]:
        return list(self.nodes_dict.keys())

    def get_edge_keys(self) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        return list(self.edges_dict.keys())

    def connected(self, u, v):
        return (u, v) in self.edges_dict
