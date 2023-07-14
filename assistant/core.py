import numpy as np
import itertools

HORIZON = 24
N_TIMESTEP = 24
N_ACTION = 4

N_VELOCITY = 100

N_POSITION = 100

POSITIONS = np.linspace(0, 7000, N_POSITION)
VELOCITIES = np.linspace(-100, 100, N_VELOCITY)

LOG_BIASED_PRIOR = np.log(np.ones(N_POSITION) / N_POSITION)


def q_transition_velocity(alpha):
    sum_col = np.sum(alpha, axis=-1)
    sum_col[sum_col <= 0.] = 1
    return alpha / sum_col[:, :, :, :, np.newaxis]


def get_new_action(number_of_step, velocity):
    pos_idx = np.absolute(POSITIONS - number_of_step).argmin()  # Something close to 0
    v_idx = np.absolute(VELOCITIES - velocity).argmin()  # Something close to 0

    for t_idx, t in enumerate(timestep):


        h = min(HORIZON, N_TIMESTEP - t_idx)
        action_plan = list(itertools.product(range(N_ACTION), repeat=h))
        n_action_plan = len(action_plan)

        # Initialize action plan values
        pragmatic = np.zeros(n_action_plan)
        epistemic = np.zeros(n_action_plan)

        q = q_transition_velocity(alpha_tavv)

        # Compute value of each action plan
        for ap_index, ap in enumerate(action_plan):

            # Initialize the rollout model
            alpha_tavv_rollout = alpha_tavv.copy()
            qv = np.zeros(n_velocity)
            qv[v_idx] = 1.
            qps = np.zeros((h, n_position))
            qp = np.zeros(n_position)
            qp[pos_idx] = 1.

            for h_idx, a in enumerate(ap):
                # Update rollout time index
                rollout_t_index = t_idx + h_idx

                # Update beliefs about the transition model
                alpha_tavv_rollout[rollout_t_index, a, :, :] += qv[:, np.newaxis] * q[rollout_t_index, a, :, :]

                # Update beliefs about the velocity and position [IMPORTANT: doing this after updating the transition model]
                qv = qv @ q[rollout_t_index, a, :, :]
                qp = qp @ (qv @ transition_position_pvp)
                qps[h_idx] = qp

            # Compute the pragmatic value of the action plan
            pragmatic[ap_index] = np.sum(qps @ LOG_PRIOR)

            # Compute the KL divergence between the model after the rollout and the current model
            epistemic[ap_index] = kl_div_dirichlet(alpha_tavv_rollout, alpha_tavv)