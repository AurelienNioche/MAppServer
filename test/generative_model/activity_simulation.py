import numpy as np
from scipy.special import expit as sigmoid


def peaked_function(x, peak_position=0, sharpness=1):
    def mirror_sigmoid(_x):
        return 1 - sigmoid(_x)
    return sigmoid(sharpness * (x - peak_position)) * mirror_sigmoid(sharpness * (x - peak_position))


def generate_nudge_effect(timestep, n_samples, seed):

    rng = np.random.default_rng(seed)
    sigma = np.eye(timestep.size) * 0.0001
    mu = peaked_function(np.linspace(-10, 10, timestep.size), 0, sharpness=1)
    effect = 100+5e4*rng.multivariate_normal(mu, sigma, size=n_samples)
    return effect


def generate_observations(
        activity_samples,
        nudge_effect,
        action_plans,
        seed
) -> (np.ndarray, np.ndarray):

    rng = np.random.default_rng(seed)
    idx = rng.integers(action_plans.shape[0], size=activity_samples.shape[0])
    actions = action_plans[idx]
    observations = activity_samples.copy()
    # TODO: Check if this is correct
    observations[:, 1:] += actions * nudge_effect[:, 1:]
    observations[observations < 0] = 0  # No negative steps
    # print(observations.shape)  N
    # print(actions.shape)       N-1
    return observations, actions
