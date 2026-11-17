from simulator.schemas.hardware import Hardware
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from simulator.schemas.base import SnapshotModel
from simulator.config import R_EARTH
from simulator.schemas.base import XYZ, LatLon

class LinkSnapshot(SnapshotModel):
    type: str
    src: str            # 链路起点卫星id
    dst: str            # 链路终点卫星id
    distance: float
    link_pos: List[XYZ]
    link_loc: Optional[List[LatLon]] = None
    snr: float
    rate: float

class Network:
    def __init__(self, number_of_planes: int, sat_datas: List[Dict[str, Any]], gs_datas: List[Dict[str, Any]], hardware: Hardware):

        self.hardware = hardware
        self.sat_datas: List[Dict[str, Any]] = sat_datas
        self.gs_datas: List[Dict[str, Any]] = gs_datas
        self.elev_threshold_deg: float = 15.0

        # 只取第一个卫星的时间序列做时间索引假设
        self.times = self.sat_datas[0]['time'] if self.sat_datas else np.array([])

        # 建立 id->索引映射，便于快速查找
        self.sat_id_to_idx = {sat['id']: i for i, sat in enumerate(sat_datas)}
        self.gs_id_to_idx = {gs['id']: i for i, gs in enumerate(gs_datas)}

        self.N = len(sat_datas)  # 卫星总数
        self.number_of_planes = number_of_planes  # 轨道平面数
        self.number_of_sat_per_planes = len(sat_datas) // number_of_planes  # 每个
        self._all_links = []  # 存储当前时刻所有链路，格式列表，后续compute_links_at更新

    @staticmethod
    def _euclidean_distance(p1, p2) -> float:
        return np.linalg.norm(np.array(p1) - np.array(p2))

    @staticmethod
    def _los_distance(h1, h2) -> float:
        # 视距极限距离（Line of Sight）
        return np.sqrt(h1 * (h1 + 2 * R_EARTH)) + np.sqrt(h2 * (h2 + 2 * R_EARTH))

    @staticmethod
    def calculate_snr(P_t: float, d: float, G_t: float, G_r: float, f: float, B: float, T_sys: float = 300.0, k_dB: float = -228.6) -> tuple[float, float]:
        """
        计算信噪比 SNR (线性值和dB值).
        :param P_t: 发射功率 (W)
        :param d: 链路距离 (m)
        :param G_t: 发射天线增益 (dB)
        :param G_r: 接收天线增益 (dB)
        :param f: 载波频率 (Hz)
        :param B: 带宽 (Hz)
        :param T_sys: 系统噪声温度 (K, 默认300)
        :param k_dB: 玻尔兹曼常数 (dBW/K/Hz, 默认-228.6)
        :return: (SNR_linear, SNR_dB)
        """
        c = 3e8
        L = 20 * np.log10(4 * np.pi * d * f / c)  # 自由空间损耗 (dB)
        EIRP = 10 * np.log10(P_t) + G_t  # dBW
        G_T = G_r - 10 * np.log10(T_sys)  # dB/K
        C_N_dB = EIRP + G_T - L - k_dB - 10 * np.log10(B)  # dB
        SNR_linear = 10 ** (C_N_dB / 10)
        return SNR_linear, C_N_dB

    @staticmethod
    def calculate_trans_rate(SNR: float, B: float) -> float:
        """
        计算传输速率 (bits/s), 基于 [1] Section II.D equation (6) (PAGE 8).
        :param SNR: 信噪比 (线性值)
        :param B: 带宽 (Hz)
        :return: 传输速率 (bits/s)
        """
        rate = B * np.log2(1 + SNR)  # bits/s, [1] equation (6)
        return rate

    def compute_isl_links_at(self, period_counter: int, slot_counter: int) -> List[LinkSnapshot]:
        links = set()

        for u in range(self.N):
            sat_u = self.sat_datas[u]
            plane_u = sat_u['plane']
            order_u = sat_u['order']
            pos_u = sat_u['space_xyz'][period_counter]
            h_u = sat_u['altitude']

            # 同轨道相邻卫星
            for offset in [-1, 1]:
                v = (u + offset) % self.number_of_sat_per_planes + plane_u * self.number_of_sat_per_planes
                if v < self.N and v != u:
                    sat_v = self.sat_datas[v]
                    pos_v = sat_v['space_xyz'][period_counter]
                    h_v = sat_v['altitude']
                    dist = self._euclidean_distance(pos_u, pos_v)
                    if dist <= self._los_distance(h_u, h_v):
                        links.add(tuple(sorted((u, v))))

            # 不同轨道同序号卫星
            for dp in [-1, 1]:
                plane_v = (plane_u + dp) % self.number_of_planes
                # 这里排除首尾相邻轨道的跨越，保持你的逻辑
                plane_abs = abs(plane_u - plane_v)
                if plane_abs == 0 or plane_abs == self.number_of_planes - 1:
                    continue
                v = plane_v * self.number_of_sat_per_planes + order_u
                if v < self.N and v != u:
                    sat_v = self.sat_datas[v]
                    order_v = sat_v['order']
                    pos_v = sat_v['space_xyz'][period_counter]
                    h_v = sat_v['altitude']
                    dist = self._euclidean_distance(pos_u, pos_v)
                    los = self._los_distance(h_u, h_v)
                    if dist <= los:
                        links.add(tuple(sorted((u, v))))

        # 转成输出格式（包含卫星id和距离）
        result: List[LinkSnapshot] = []
        for u, v in sorted(links):
            sat_u = self.sat_datas[u]
            sat_v = self.sat_datas[v]
            pos_u = sat_u['space_xyz'][period_counter]
            pos_v = sat_v['space_xyz'][period_counter]
            loc_u = sat_u['subpoint_latlon'][period_counter]
            loc_v = sat_v['subpoint_latlon'][period_counter]
            dist = self._euclidean_distance(pos_u, pos_v)

            # 计算SNR和传输速率 (ISL默认参数, [1] Table II PAGE 23)
            snr_linear, snr_dB = self.calculate_snr(self.hardware.isl_tx_power_w, dist, self.hardware.isl_gain_tx_dbi, self.hardware.isl_gain_rx_dbi, self.hardware.isl_frequency_hz, self.hardware.isl_bandwidth_hz, T_sys=self.hardware.isl_noise_temp_k)
            rate = self.calculate_trans_rate(snr_linear, self.hardware.isl_bandwidth_hz)

            result.append(
                LinkSnapshot(
                    type='ISL',
                    src=sat_u['id'],
                    dst=sat_v['id'],
                    distance=dist,
                    link_pos=[XYZ(x=pos_u[0], y=pos_u[1], z=pos_u[2]),
                             XYZ(x=pos_v[0], y=pos_v[1], z=pos_v[2])],
                    link_loc=[LatLon(lat=loc_u[0], lon=loc_u[1]),
                             LatLon(lat=loc_v[0], lon=loc_v[1])],
                    snr=snr_dB,  # 新增SNR
                    rate=rate,  # 新增传输速率 (bits/s)
                )
            )

        return result

    def compute_sgl_links_at(self, period_counter: int, slot_counter: int) -> List[LinkSnapshot]:
        """
        计算时刻t所有DL和UL链路（卫星<->地面站）。
        判断方法基于卫星相对于地面站的仰角，超过阈值即存在链路。
        """
        links: List[LinkSnapshot] = []
        for i_sat, sat in enumerate(self.sat_datas):
            # ensure numpy arrays for position and latlon
            pos_sat = np.asarray(sat['space_xyz'][period_counter])
            loc_sat = np.asarray(sat['subpoint_latlon'][period_counter])
            id_sat = sat['id']

            for i_gs, gs in enumerate(self.gs_datas):
                pos_gs = np.asarray(gs['xyz'][period_counter])
                loc_gs = np.asarray(gs['latlon'])
                id_gs = gs['id']

                # Validate lat/lon shapes: require at least two elements (lat, lon)
                if loc_sat.size < 2 or loc_gs.size < 2:
                    # skip malformed entries
                    continue

                # 向量从地面站指向卫星
                vec = pos_sat - pos_gs
                # protect against zero-length vectors
                norm_vec = np.linalg.norm(vec)
                if norm_vec == 0:
                    continue
                gs_norm = pos_gs / np.linalg.norm(pos_gs)
                elev_rad = np.arcsin(np.dot(vec, gs_norm) / norm_vec)
                elev_deg = np.degrees(elev_rad)

                if elev_deg > self.elev_threshold_deg:
                    dist = norm_vec

                    # 计算SNR和传输速率 (SGL默认参数, [1] Table II PAGE 23)
                    snr_down_linear, snr_down_dB = self.calculate_snr(self.hardware.downlink_tx_power_w, dist, self.hardware.downlink_gain_tx_dbi, self.hardware.downlink_gain_rx_dbi, self.hardware.downlink_frequency_hz, self.hardware.downlink_bandwidth_hz, T_sys=self.hardware.downlink_noise_temp_k)
                    rate_down = self.calculate_trans_rate(snr_down_linear, self.hardware.downlink_bandwidth_hz)

                    # 下行链路
                    links.append(
                        LinkSnapshot(
                            type='DL',
                            src=id_sat,
                            dst=id_gs,
                            distance=dist,
                            link_pos=[XYZ(x=float(pos_sat[0]), y=float(pos_sat[1]), z=float(pos_sat[2])),
                                     XYZ(x=float(pos_gs[0]), y=float(pos_gs[1]), z=float(pos_gs[2]))],
                            link_loc=[LatLon(lat=float(loc_sat[0]), lon=float(loc_sat[1])),
                                     LatLon(lat=float(loc_gs[0]), lon=float(loc_gs[1]))],
                            snr=snr_down_dB,
                            rate=rate_down,
                        )
                    )

                    # 上行链路 (假设参数类似, P_t低)
                    snr_up_linear, snr_up_dB = self.calculate_snr(self.hardware.uplink_tx_power_w, dist, self.hardware.uplink_gain_rx_dbi, self.hardware.uplink_gain_tx_dbi, self.hardware.uplink_frequency_hz, self.hardware.uplink_bandwidth_hz, T_sys=self.hardware.uplink_noise_temp_k)
                    rate_up = self.calculate_trans_rate(snr_up_linear, self.hardware.uplink_bandwidth_hz)

                    links.append(
                        LinkSnapshot(
                            type='UL',
                            src=id_gs,
                            dst=id_sat,
                            distance=dist,
                            link_pos=[XYZ(x=float(pos_gs[0]), y=float(pos_gs[1]), z=float(pos_gs[2])),
                                     XYZ(x=float(pos_sat[0]), y=float(pos_sat[1]), z=float(pos_sat[2]))],
                            link_loc=[LatLon(lat=float(loc_gs[0]), lon=float(loc_gs[1])),
                                     LatLon(lat=float(loc_sat[0]), lon=float(loc_sat[1]))],
                            snr=snr_up_dB,
                            rate=rate_up,
                        )
                    )

        return links

    def _at(self, period_counter: int, slot_counter: int):
        """
        计算时刻 t 所有链路，更新 self.allLinks
        """
        isl_links = self.compute_isl_links_at(period_counter, slot_counter)
        sgl_links = self.compute_sgl_links_at(period_counter, slot_counter)
        self._all_links = isl_links + sgl_links

    def is_link_exist_at(self, src: str, dst: str, period_counter: int, slot_counter: int) -> bool:
        """
        判断在时刻 t，id1 和 id2 是否存在链路（ISL 或 UL/DL）。
        """
        self._at(period_counter, slot_counter)
        for l in self._all_links:
            if (l.src == src and l.dst == dst) or (l.src == dst and l.dst == src):
                return True
        return False

    def get_link_data_at(self, id1: str, id2: str, period_counter: int, slot_counter: int) -> Optional[dict]:
        self._at(period_counter, slot_counter)
        for l in self._all_links:
            # if (link['src'] == id1 and link['dst'] == id2) or (link['src'] == id2 and link['dst'] == id1):
            if (l.src == id1 and l.dst == id2) or (l.src == id2 and l.dst == id1):
                return l
        return None

    def get_links_of_node_at(self, node_id: str, node_type: str, period_counter: int, slot_counter: int) -> List[LinkSnapshot]:
        self._at(period_counter, slot_counter)
        result = []

        for l in self._all_links:
            if node_type.upper() == "SAT":
                if l.src == node_id or l.dst == node_id and l.type == "ISL":
                    result.append(l)
            elif node_type.upper() == "GS":
                if (l.src == node_id or l.dst == node_id) and l.type in ("DL", "UL"):
                    result.append(l)
            else:
                if (l.src == node_id or l.dst == node_id):
                    result.append(l)

        return result

    def get_isl_of_node_at(self, sat_id: str, period_counter: int, slot_counter: int) -> List[LinkSnapshot]:
        self._at(period_counter, slot_counter)
        result = []

        for l in self._all_links:
            if l.type == "ISL" and (l.src == sat_id or l.dst == sat_id):
                result.append(l)

        return result

    def get_sgl_of_node_at(self, node_id: str, node_type: str, period_counter: int, slot_counter: int) -> List[LinkSnapshot]:
        self._at(period_counter, slot_counter)
        result = []

        for l in self._all_links:
            if node_type.upper() == "GS":
                if (l.src == node_id or l.dst == node_id) and l.type in ("DL", "UL"):
                    result.append(l)
            elif node_type.upper() == "SAT":
                if (l.src == node_id or l.dst == node_id) and l.type in ("DL", "UL"):
                    result.append(l)

        return result

    def snapshot(self) -> tuple[LinkSnapshot, ...]:
        return tuple(link.model_copy(deep=True) for link in self._all_links)

    def serialize(self) -> list[dict]:
        return [link.model_dump(mode="json") for link in self.snapshot()]
