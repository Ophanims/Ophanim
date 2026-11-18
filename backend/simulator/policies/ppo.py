"""A loaded PPO model produces the complete slot's scheduling actions."""
from simulator.policies.discrete_scheduler import DiscreteScheduler


class PPOPolicy:
    def __init__(self, project):
        from simulator.services.policy_loader import load_model_and_normalizer
        from simulator.services.model_paths import model_path_for_project
        self.model, self.normalizer = load_model_and_normalizer(model_path_for_project(project.project_id))
        self.selection_reward = 0.0
        from simulator.env.core.observation import get_obs_space_shape
        expected = get_obs_space_shape(project.constellation.number_of_sat_per_planes,
                                       project.constellation.number_of_planes)
        if self.model.observation_space != expected:
            raise ValueError("PPO checkpoint dimensions do not match this constellation; train a compatible model")

    def __deepcopy__(self, memo):
        candidate = object.__new__(type(self))
        candidate.__dict__ = self.__dict__.copy()
        memo[id(self)] = candidate
        return candidate

    def decide(self, view, context):
        from simulator.env.core.observation import get_obs_space_shape
        expected = get_obs_space_shape(view.entity_collection.number_of_sat_per_planes,
                                       view.entity_collection.number_of_planes)
        if self.model.observation_space != expected:
            raise ValueError("PPO checkpoint dimensions do not match this constellation; train a compatible model")
        scheduler = DiscreteScheduler()
        scheduler.begin(view)
        self.selection_reward = 0.0
        while not scheduler.finished:
            observation = scheduler.observation()
            if self.normalizer is not None:
                observation = self.normalizer.normalize_obs(observation)
            action, _ = self.model.predict(observation, deterministic=True, action_masks=scheduler.action_masks())
            self.selection_reward += scheduler.submit(action)
        return scheduler.actions()

    def evaluate(self, before, simulator, actions, context):
        from simulator.policies.reward import transition_reward
        return transition_reward(before, simulator, actions, context, self.selection_reward)
