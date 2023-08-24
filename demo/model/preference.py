import numpy as np
from scipy.stats import norm


def compute_log_prior(
        position,
        target=None,
        tolerance=0.5):
    """
    Compute log prior for a given parameter vector.
    """

    if target is None:
        target = max(position)

    # Compute log prior
    p = norm.cdf(position, loc=target, scale=tolerance)
    p /= p.sum()
    return np.log(p)

