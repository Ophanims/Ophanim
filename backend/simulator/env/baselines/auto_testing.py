"""Evaluate policies through the same session, snapshot and record path as the UI."""
import json
from typing import Literal
from simulator.core.session import SimulationSession
from simulator.schemas.base import SnapshotModel
from simulator.schemas.project import Project
from simulator.services.session_records import SessionRecord
from simulator.settings import SIMULATION_OUTPUT_DIR


class EvaluationResult(SnapshotModel):
    project_id: str
    record_id: str
    algorithm: str
    frame_count: int
    completed_task_count: int
    total_reward: float
    average_battery_ratio: float
    average_latency_s: float
    status: Literal["completed", "failed"]


class AutoTester:
    def __init__(self, project: Project, algorithms: tuple[str, ...] = ("ppo",)):
        self.project = project.snapshot()
        self.algorithms = algorithms
        self.results: list[EvaluationResult] = []

    def snapshot(self) -> tuple[EvaluationResult, ...]:
        return tuple(result.snapshot() for result in self.results)

    def run(self) -> None:
        for algorithm in self.algorithms:
            session = SimulationSession(self.project, algorithm)
            record = SessionRecord(self.project, algorithm)
            total_reward = 0.0
            status = "failed"
            try:
                state = session.snapshot()
                record.append_state(state)
                while not session.is_completed:
                    state = session.step()
                    record.append_state(state)
                    total_reward += state.info.reward
                status = "completed"
                completed = [task for task in state.tasks if task.is_done]
                average_latency_s = sum((task.t_end - task.t_start) for task in completed) * session.environment.slot_in_num / len(completed) if completed else 0
                self.results.append(EvaluationResult(
                    project_id=self.project.project_id, record_id=record.record_id, algorithm=algorithm,
                    frame_count=record.frame_count, completed_task_count=len(completed), total_reward=total_reward,
                    average_battery_ratio=sum(satellite.battery_percent for satellite in state.satellites) / (100 * len(state.satellites)) if state.satellites else 0,
                    average_latency_s=average_latency_s, status=status,
                ))
            finally:
                record.close(status)
                session.close()
            directory = SIMULATION_OUTPUT_DIR / "evaluations"
            directory.mkdir(parents=True, exist_ok=True)
            (directory / f"{record.record_id}.json").write_text(self.results[-1].model_dump_json(indent=2))
