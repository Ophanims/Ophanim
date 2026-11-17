"""Managed optional ML jobs; terminate owned subprocesses on application shutdown."""
import multiprocessing
from typing import Literal
from uuid import uuid4
from simulator.schemas.base import SnapshotModel
from simulator.schemas.project import Project


class JobSnapshot(SnapshotModel):
    job_id: str
    job_type: Literal["train", "auto_test"]
    status: Literal["running", "completed", "failed", "cancelled"]
    exit_code: int | None = None


def run_job(project: dict, job_type: str) -> None:
    project = Project.model_validate(project)
    if job_type == "train":
        from simulator.env.train_and_run import train_model
        train_model(project)
    else:
        from simulator.env.baselines.auto_testing import AutoTester
        AutoTester(project).run()


class BackgroundJobs:
    def __init__(self):
        self._jobs = {}
        self._cancelled = set()

    def start_job(self, project: Project, job_type: str) -> JobSnapshot:
        import importlib.util
        if importlib.util.find_spec("sb3_contrib") is None:
            raise ImportError("Install backend/requirements-ml.txt")
        if any(process.is_alive() for _, process in self._jobs.values()):
            raise ValueError("Another ML job is running; wait or cancel it first")
        job_id = uuid4().hex
        process = multiprocessing.get_context("spawn").Process(
            target=run_job, args=(project.serialize(), job_type), daemon=True,
        )
        process.start()
        self._jobs[job_id] = (job_type, process)
        return self.snapshot(job_id)

    def snapshot(self, job_id: str) -> JobSnapshot:
        job_type, process = self._jobs[job_id]
        status = "cancelled" if job_id in self._cancelled else "running" if process.is_alive() else "completed" if process.exitcode == 0 else "failed"
        return JobSnapshot(job_id=job_id, job_type=job_type, status=status, exit_code=process.exitcode)

    def cancel_job(self, job_id: str) -> JobSnapshot:
        _, process = self._jobs[job_id]
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)
            if process.is_alive():
                process.kill()
                process.join(timeout=5)
            self._cancelled.add(job_id)
        return self.snapshot(job_id)

    def close(self) -> None:
        for job_id in self._jobs:
            self.cancel_job(job_id)


jobs = BackgroundJobs()
