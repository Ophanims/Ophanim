"""Project the canonical live snapshot into queryable analysis columns."""
from psycopg.types.json import Jsonb
from simulator.services.record_contracts import NetworkMetrics

ENTITY_TABLES = {"satellites": "satellite_states", "stations": "station_states",
                 "tasks": "task_states", "missions": "mission_states",
                 "links": "link_states", "network": "network_metrics"}


def insert_analysis_points(cursor, record_id, states):
    rows = {kind: [] for kind in ENTITY_TABLES}
    for state in states:
        prefix = (state.time, record_id, state.frame_counter)
        for satellite in state.satellites:
            rows["satellites"].append((*prefix, satellite.id, satellite.battery_percent,
                                       satellite.task_queue, Jsonb(satellite.serialize())))
        for station in state.stations:
            rows["stations"].append((*prefix, station.id, station.on_upload,
                                     station.on_download, Jsonb(station.serialize())))
        for task in state.tasks:
            rows["tasks"].append((*prefix, str(task.id), task.is_done,
                                  task.workload_percent, Jsonb(task.model_dump(mode="json"))))
        for mission in state.missions:
            rows["missions"].append((*prefix, str(mission.id), mission.status,
                                     mission.position, Jsonb(mission.serialize())))
        for link in state.links:
            rows["links"].append((*prefix, link.type, link.src, link.dst, link.distance,
                                  link.snr, link.rate, Jsonb(link.serialize())))
        metrics = NetworkMetrics(num_nodes=len(state.satellites) + len(state.stations),
            num_edges=len(state.links), num_tasks=len(state.tasks) + len(state.missions),
            reward=state.info.reward,
            average_battery_percent=sum(s.battery_percent for s in state.satellites) / len(state.satellites) if state.satellites else 0)
        rows["network"].append((*prefix, metrics.num_nodes, metrics.num_edges,
                                metrics.num_tasks, metrics.reward, metrics.average_battery_percent, Jsonb(metrics.serialize())))
    for kind, points in rows.items():
        if points:
            # Table names and row shapes are internal constants, never HTTP input.
            placeholders = ", ".join(["%s"] * len(points[0]))
            cursor.executemany(f"INSERT INTO {ENTITY_TABLES[kind]} VALUES ({placeholders}) ON CONFLICT DO NOTHING", points)
