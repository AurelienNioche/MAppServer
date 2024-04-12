import numpy as np
from scipy import stats


def normalize_last_dim(alpha):
    sum_col = np.sum(alpha, axis=-1)
    sum_col[sum_col <= 0.0] = 1
    return alpha / np.expand_dims(sum_col, axis=-1)


def compute_deriv_cum_steps(step_events, timestep) -> (list[float], list[float]):

    # X_train = []
    # y_train = []
    deriv_cum_steps = np.zeros((len(step_events), timestep.size))
    for idx_day, step_events_day in enumerate(step_events):
        cum_steps_day = np.sum(step_events_day <= timestep[:, None], axis=1)
        deriv_cum_steps_day = np.gradient(cum_steps_day, timestep+1) / (timestep.size-1)
        deriv_cum_steps[idx_day] = deriv_cum_steps_day
        # X_train.append(list(timestep))
        # y_train.append(list(deriv_cum_steps_day))
    # return X_train, y_train
    return deriv_cum_steps


def build_pseudo_count_matrix(
        actions: np.ndarray,
        observations: np.ndarray,
        timestep: np.ndarray,
        velocity: np.ndarray,
        jitter: float = 1e-6
) -> np.ndarray:
    """
    Build the pseudo-count matrix for the generative model
    """
    # Compute the number of actions
    n_actions = np.unique(actions).size
    # Add one bin for infinity
    bins = np.concatenate((velocity, np.full(1, np.inf)))
    # Clip the activity to the bins
    drv = np.clip(observations, bins[0], bins[-1])
    # Compute the index of the bins
    v_idx = np.digitize(drv, bins, right=False) - 1
    # Initialize the pseudo-count matrix
    alpha_atvv = np.zeros((n_actions, timestep.size-1, velocity.size, velocity.size))
    for sample in range(actions.shape[0]):
        for t in range(timestep.size - 1):
            alpha_atvv[actions[sample, t], t, v_idx[sample, t], v_idx[sample, t + 1]] += 1

    alpha_atvv += jitter
    return alpha_atvv


def build_position_transition_matrix(
        position: np.ndarray,
        velocity: np.ndarray,
        sigma_transition_position: float = 1e-3
) -> np.ndarray:
    # Compute position transition matrix
    tr = np.zeros((position.size, velocity.size, position.size))
    for p_idx, p in enumerate(position):
        for v_idx, v in enumerate(velocity):
            dist = stats.norm.pdf(position, loc=p + v, scale=sigma_transition_position)
            if np.sum(dist) == 0:
                if p + v < 0:
                    dist[0] = 1
                elif p + v > position[-1]:
                    dist[-1] = 1 # All weight on greatest position
                else:
                    print(f"bounds: {position[0]}, {position[-1]}")
                    print(f"p+v: {p+v}")
                    raise ValueError("This should not happen, try increasing 'sigma_transition_position'")
            tr[p_idx, v_idx, :] = dist

    transition_position_pvp = normalize_last_dim(tr)

    # Make sure that all probabilities sum to (more or less) one
    np.allclose(np.sum(transition_position_pvp, axis=-1), 1)
    return transition_position_pvp
