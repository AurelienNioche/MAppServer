import numpy as np
import itertools
from scipy.special import gammaln, digamma
from datetime import datetime

from config import HORIZON, N_TIMESTEP, N_ACTION, N_VELOCITY, N_POSITION, POSITIONS, VELOCITIES, LOG_BIASED_PRIOR
from . models import Velocity, Position, Alpha


def kl_div_dirichlet(alpha_coeff, beta_coeff):
    """
        https://statproofbook.github.io/P/dir-kl.html
    """
    alpha_0 = np.sum(alpha_coeff)
    beta_0 = np.sum(beta_coeff)
    kl = (
        gammaln(alpha_0)
        - gammaln(beta_0)
        - np.sum(gammaln(alpha_coeff))
        + np.sum(gammaln(beta_coeff))
        + np.sum((alpha_coeff - beta_coeff) * (digamma(alpha_coeff) - digamma(alpha_0)))
    )
    return kl


def q_transition_velocity(alpha):
    sum_col = np.sum(alpha, axis=-1)
    sum_col[sum_col <= 0.] = 1
    return alpha / sum_col[:, :, :, :, np.newaxis]


def get_new_action(user):
    # return np.random.randint(0, N_ACTION)
    number_of_step = 0

    now = datetime.now()

    alpha_tapvv = np.zeros((N_TIMESTEP, N_ACTION, N_POSITION, N_VELOCITY, N_VELOCITY))
    for e in Alpha.objects.filter(user=user):
        alpha_tapvv[:, :, :, :] += e.alpha

    velocity = Velocity.objects.filter(user=user, dt__date=now.date).order_by('-timestep_idx')[0].velocity

    _get_new_action(number_of_step, velocity, alpha_tavv, transition_position_pvp, timestep)


def _get_new_action(number_of_step, velocity, alpha_tavv, transition_position_pvp, timestep):

    pos_idx = np.absolute(POSITIONS - number_of_step).argmin()
    v_idx = np.absolute(VELOCITIES - velocity).argmin()

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
            qv = np.zeros(N_VELOCITY)
            qv[v_idx] = 1.
            qps = np.zeros((h, N_POSITION))
            qp = np.zeros(N_POSITION)
            qp[pos_idx] = 1.

            for h_idx, a in enumerate(ap):
                # Update rollout time index
                rollout_t_index = t_idx + h_idx

                # Update beliefs about the transition model
                alpha_tavv_rollout[rollout_t_index, a, :, :] += qv[:, np.newaxis] * q[rollout_t_index, a, :, :]

                # Update beliefs about the velocity and position
                # [IMPORTANT: updating the beliefs transition model BEFORE doing this]
                qv = qv @ q[rollout_t_index, a, :, :]
                qp = qp @ (qv @ transition_position_pvp)
                qps[h_idx] = qp

            # Compute the pragmatic value of the action plan
            pragmatic[ap_index] = np.sum(qps @ LOG_BIASED_PRIOR)

            # Compute the KL divergence between the model after the rollout and the current model
            epistemic[ap_index] = kl_div_dirichlet(alpha_tavv_rollout, alpha_tavv)

        val = pragmatic + epistemic
        best_action_plan_indexes = np.arange(n_action_plan)[val == val.max()]
        selected_action_plan_idx = np.random.choice(best_action_plan_indexes)
        a = action_plan[selected_action_plan_idx][0]

        return a


def learn():

    pass
