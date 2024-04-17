import numpy as np

from . helpers import peaked_function


def generate_nudge_effect(timestep, n_samples):

    sigma = np.eye(timestep.size) * 0.0001
    rng = np.random.default_rng(1234)
    mu = peaked_function(np.linspace(-10, 10, timestep.size), 0, sharpness=1)
    effect = 100+5e4*rng.multivariate_normal(mu, sigma, size=n_samples)
    return effect


def generate_observations(
        activity_samples,
        nudge_effect,
        action_plans) -> (np.ndarray, np.ndarray):

    idx = np.random.randint(action_plans.shape[0], size=activity_samples.shape[0])
    actions = action_plans[idx]
    observations = activity_samples.copy()
    observations[:, 1:] += actions * nudge_effect[:, 1:]
    observations[observations < 0] = 0  # No negative steps
    print(observations.shape)
    print(actions.shape)
    return observations, actions
