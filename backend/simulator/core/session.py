"""Owns one simulation; algorithms never retain another session's state."""
from simulator.contracts import RunInfo, SimulationSnapshot
from simulator.core.simulation import Simulation
from simulator.schemas.project import Project


class SimulationSession:
    def __init__(self, project: Project, algorithm: str = "geometry"):
        self.algorithm = algorithm
        self.info = RunInfo()
        self.model = None
        self.normalizer = None
        if algorithm == "geometry":
            self.environment = Simulation()
            self.environment.setup(project)
        else:
            self.environment = self._create_environment(project, algorithm)
            result = self.environment.reset()
            self.observation = result[0] if isinstance(result, tuple) else result
            if self.model is not None and self.model.observation_space != self.environment.observation_space:
                self.close()
                raise ValueError("PPO checkpoint dimensions do not match this constellation; train a compatible model")
        self.is_completed = False

    def _create_environment(self, project: Project, algorithm: str):
        if algorithm == "ophanim":
            from simulator.core.physics_environment import PhysicsEnvironment
            return PhysicsEnvironment(project)
        if algorithm == "ppo":
            from simulator.env.ppo.ppo_env import PPOEnv
            from simulator.services.policy_loader import load_model_and_normalizer
            from simulator.services.model_paths import model_path_for_project
            # Model loading remains optional for geometry and baseline sessions.
            self.model, self.normalizer = load_model_and_normalizer(model_path_for_project(project.project_id))
            return PPOEnv(project)
        if algorithm == "l2d2":
            from simulator.env.baselines.l2d2.l2d2_env import L2D2Env
            return L2D2Env(project)
        if algorithm == "phoenix":
            from simulator.env.baselines.phoenix.phoenix_env import PhoenixEnv
            return PhoenixEnv(project)
        if algorithm == "mhspo":
            from simulator.env.baselines.mhspo.mhspo_env import MHSPOEnv
            return MHSPOEnv(project)
        raise ValueError("Unknown algorithm")

    def step(self) -> SimulationSnapshot:
        if self.is_completed:
            return self.snapshot()
        if self.algorithm == "geometry":
            self.is_completed, info = self.environment.step()
        else:
            if self.algorithm == "ppo":
                observation = self.normalizer.normalize_obs(self.observation) if self.normalizer else self.observation
                actions, _ = self.model.predict(observation, deterministic=True,
                                                action_masks=self.environment.action_masks())
                result = self.environment.step(actions)
                self.observation, reward, terminated, truncated, info = result
            else:
                reward, terminated, truncated, info = self.environment.step()
            self.is_completed = bool(terminated or truncated)
        self.info = RunInfo.model_validate(info)
        if self.environment.time_recorder >= self.environment.t_end:
            self.is_completed = True
        return self.snapshot()

    def snapshot(self) -> SimulationSnapshot:
        environment = self.environment
        if self.algorithm == "ophanim":
            state = environment.snapshot()
            return state.model_copy(update={"info": self.info}) if self.environment.frame_counter else state
        tasks = environment.task_manager.tasks if hasattr(environment, "task_manager") else []
        return SimulationSnapshot(
            time=environment.time_recorder.isoformat(), frame_counter=environment.frame_counter,
            slot_counter=environment.slot_counter, max_slot_number=environment.max_slot_number,
            period_counter=environment.period_counter, max_period_numbers=environment.max_period_numbers,
            satellites=tuple(entity.snapshot() for entity in environment.sat),
            stations=tuple(entity.snapshot() for entity in environment.gs),
            rois=tuple(entity.snapshot() for entity in environment.roi),
            links=tuple(link.model_copy(deep=True) for link in environment.net._all_links),
            sun=environment.sun.snapshot(), earth=environment.eth.snapshot(),
            tasks=tuple(task.model_copy(deep=True) for task in tasks), info=self.info,
        ).model_copy(deep=True)

    def close(self) -> None:
        logger = getattr(self.environment, "logger", None)
        if logger is not None and hasattr(logger, "close"):
            logger.close()
        if hasattr(self.environment, "close"):
            self.environment.close()
