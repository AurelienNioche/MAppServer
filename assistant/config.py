import numpy as np
from scipy.stats import norm

HORIZON = 24
N_ACTION = 4

DT = 60 * 30  # 30 minutes
MAX_TS = 60 * 60 * 24  # 24 hours
TIMESTEP = np.arange(0, MAX_TS + np.finfo(np.float64).eps, DT)
N_TIMESTEP = len(TIMESTEP)

DP = 500
MAX_P = 10000
POSITIONS = np.arange(0, MAX_P+np.finfo(np.float64).eps, DP)
N_POSITION = len(POSITIONS)

DV = 0.2
MAX_VEL = 2.0
VELOCITIES = np.arange(0, MAX_VEL+np.finfo(np.float64).eps, DV)
N_VELOCITY = len(VELOCITIES)

TRANSITION_POSITION_PVP = np.zeros((N_POSITION, N_VELOCITY, N_POSITION))
for p_idx, p in enumerate(POSITIONS):
    for v_idx, v in enumerate(VELOCITIES):
        for p2_idx, p2 in enumerate(POSITIONS):
            TRANSITION_POSITION_PVP[p_idx, v_idx, p2_idx] = norm.pdf(p2, loc=p + DT*v, scale=0.1)

sum_col = TRANSITION_POSITION_PVP.sum(axis=-1)
TRANSITION_POSITION_PVP /= sum_col[:, :, np.newaxis]

LOG_BIASED_PRIOR = np.log(np.ones(N_POSITION) / N_POSITION)

EXPERIMENT = "active-inference"
