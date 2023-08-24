import numpy as np
from scipy.stats import norm


def compute_transition_velocity_matrix(
    timestep, position, velocity, action, friction_factor, n_sample, seed):
    """
    Transition matrix for velocity (dimensions: t a p v v)
    :param n_sample:
    :param friction_factor:
    :param timestep:
    :param position:
    :param velocity:
    :param action:
    :return:
    """

    np.random.seed(seed)

    def rbf(_x, alpha=0.05, length=0.1):
        sq_dist = (
            np.sum(_x**2, axis=1)[:, None]
            + np.sum(_x**2, axis=1)[None, :]
            - 2 * np.dot(_x, _x.T)
        )
        sigma = alpha**2 * np.exp(-0.5 * sq_dist / length**2)
        return sigma

    assert len(action) == 2, "Only two actions are supported"

    n_timestep = len(timestep)
    n_position = len(position)
    n_velocity = len(velocity)
    n_action = len(action)

    x = np.column_stack([x.ravel() for x in np.meshgrid(timestep, position)])

    mu = np.zeros((2, n_timestep * n_position))
    mu[0] = 0.8 + 0.6 * np.cos(6 * x[:, 0] - 2)  # + 0.3*np.sin(4*x[:,1] + 3)
    mu[1] = 0.8 + 0.7 * np.cos(3 * x[:, 0] - 4)  # + 0.3*np.sin(4*x[:,1] + 3)

    transition_velocity_tapvv = np.zeros(
        (n_timestep, n_action, n_position, n_velocity, n_velocity)
    )
    for a in action:
        force = np.random.multivariate_normal(mu[a], rbf(x), size=n_sample)
        force = force.reshape(n_sample, n_timestep, n_position)

        for v_idx, v in enumerate(velocity):
            for t_idx, t in enumerate(timestep):
                for p_idx, p in enumerate(position):

                    new_v = np.zeros(n_sample)
                    new_v += v - friction_factor * v
                    new_v += force[:, t_idx, p_idx]
                    new_v = np.clip(new_v, min(velocity), max(velocity))
                    hist, bins = np.histogram(
                        new_v, bins=list(velocity) + [2 * velocity[-1] - velocity[-2]]
                    )
                    sum_hist = np.sum(hist)
                    if sum_hist > 0:
                        density = hist / sum_hist
                    else:
                        density = hist
                    transition_velocity_tapvv[t_idx, a, p_idx, v_idx, :] = density

    return transition_velocity_tapvv


def compute_transition_position_matrix(timestep, position, velocity):
    """
    Transition matrix for position (dimensions: p v p)
    :return:
    """
    n_timestep = len(timestep)
    n_position = len(position)
    n_velocity = len(velocity)

    transition_position_pvp = np.zeros((n_position, n_velocity, n_position))
    dt = (max(timestep) - min(timestep)) / (n_timestep - 1)
    dp = (max(position) - min(position)) / (n_position - 1)
    for p_idx, p in enumerate(position):
        for v_idx, v in enumerate(velocity):
            for p2_idx, p2 in enumerate(position):
                transition_position_pvp[p_idx, v_idx, p2_idx] = norm.pdf(
                    p2, loc=p + dt * v, scale=dp / 4
                )
            denominator = transition_position_pvp[p_idx, v_idx, :].sum()
            if denominator == 0:
                # Handle division by zero here
                # For example, set the result to a specific value
                transition_position_pvp[p_idx, v_idx, :] = 0
            else:
                transition_position_pvp[p_idx, v_idx, :] /= denominator
    return transition_position_pvp
