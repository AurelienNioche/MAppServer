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
    effect[effect < 0] = 0
    return effect


def generate_observations(
        cum_steps,
        nudge_effect,
        action_plans,
        seed
) -> (np.ndarray, np.ndarray):

    # First compute the pseudo-derivative
    steps = np.concatenate((cum_steps[:, 0:1], np.diff(cum_steps, axis=1)), axis=1)
    # Then add the nudge effect
    rng = np.random.default_rng(seed)
    idx = rng.integers(action_plans.shape[0], size=steps.shape[0])
    actions = action_plans[idx]
    steps[:] += actions * nudge_effect[:]
    steps[steps < 0] = 0  # No negative steps
    # Then re-compute the cumulative sum
    cum_steps = np.cumsum(steps, axis=1)
    return cum_steps, actions
