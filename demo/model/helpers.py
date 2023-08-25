import numpy as np
from scipy.special import digamma, gammaln


def compute_q(alpha):
    sum_col = np.sum(alpha, axis=-1)
    sum_col[sum_col <= 0.] = 1
    return alpha / np.expand_dims(sum_col, axis=-1)


def kl_div_dirichlet(alpha_coeff, beta_coeff):
    """
    Compute KL divergence between two Dirichlet distributions.
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


def compute_sum_kl_div_dirichlet(alpha_rollout, alpha):
    # sum_kl = 0
    # for a_idx in range(n_action):
    #     for p_idx in range(n_position):
    #         for v_idx in range(n_velocity):
    #             for t_idx in range(n_timestep):
    #                 alpha_coeff = alpha_tapvv_rollout[t_idx, a_idx, p_idx, v_idx, :]
    #                 beta_coeff = alpha_tapvv[t_idx, a_idx, p_idx, v_idx, :]
    #                 alpha_0 = np.sum(alpha_coeff)
    #                 beta_0 = np.sum(beta_coeff)
    #                 kl = (
    #                     gammaln(alpha_0)
    #                     - gammaln(beta_0)
    #                     - np.sum(gammaln(alpha_coeff))
    #                     + np.sum(gammaln(beta_coeff))
    #                     + np.sum((alpha_coeff - beta_coeff) * (digamma(alpha_coeff) - digamma(alpha_0)))
    #                 )
    #                 sum_kl += kl
    # return sum_kl
    alpha_0 = np.sum(alpha_rollout, axis=-1)
    beta_0 = np.sum(alpha, axis=-1)
    sum_kl = np.sum(
        gammaln(alpha_0)
        - gammaln(beta_0)
        - np.sum(gammaln(alpha_rollout), axis=-1)
        + np.sum(gammaln(alpha), axis=-1)
        + np.sum(
            (alpha_rollout - alpha)
            * (digamma(alpha_rollout) - digamma(alpha_0[..., np.newaxis])),
            axis=-1,
        )
    )
    return sum_kl
