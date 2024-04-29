import numpy as np



def square_exponential_kernel(x, alpha, length):
    if len(x.shape) == 1:
        x = x.reshape(-1, 1)
    sq_dist = np.sum(x**2, 1).reshape(-1, 1) + np.sum(x**2, 1) - 2 * np.dot(x, x.T)
    return alpha**2 * np.exp(-0.5 * sq_dist / length**2)
