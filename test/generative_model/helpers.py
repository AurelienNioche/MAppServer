import numpy as np
from scipy.special import expit as sigmoid


def square_exponential_kernel(x, alpha, length):
    if len(x.shape) == 1:
        x = x.reshape(-1, 1)
    sq_dist = np.sum(x**2, 1).reshape(-1, 1) + np.sum(x**2, 1) - 2 * np.dot(x, x.T)
    return alpha**2 * np.exp(-0.5 * sq_dist / length**2)


def peaked_function(x, peak_position=0, sharpness=1):
    def mirror_sigmoid(_x):
        return 1 - sigmoid(_x)
    return sigmoid(sharpness * (x - peak_position)) * mirror_sigmoid(sharpness * (x - peak_position))
