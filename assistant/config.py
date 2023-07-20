import numpy as np

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

LOG_BIASED_PRIOR = np.log(np.ones(N_POSITION) / N_POSITION)

EXPERIMENT = "active-inference"
