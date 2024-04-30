import os
from datetime import datetime
import numpy as np
from scipy.special import softmax
from pytz import timezone

from MAppServer.settings import TIME_ZONE

URL = "ws://127.0.0.1:8080/ws"
USERNAME = "123test"
INIT_STATE = "experimentNotStarted"
# WHen things will start
FIRST_CHALLENGE_OFFER = "7:00"
# Define "now" for debug purposes
NOW_TIME = "00:00"
NOW = datetime.combine(
    datetime.now().date(),
    datetime.strptime(NOW_TIME, "%H:%M").time(),
    tzinfo=timezone(TIME_ZONE)
)
# Starting date of the experiment
STARTING_DATE = NOW.date().strftime("%d/%m/%Y")  # "28/03/2024"
# Experiment name (can be anything)
EXPERIMENT_NAME = "not-even-an-alpha-test"
# Amount of money already in the chest
BASE_CHEST_AMOUNT = 6
OBJECTIVE = 10
# Amount of reward (in pounds) for each challenge completed
AMOUNT = 0.4
OFFER_WINDOW = 1   # in hours
CHALLENGE_WINDOW = 2  # in hours
CHALLENGE_DURATION = 1  # in hours
N_CHALLENGE = 3
# NGROK_URL = "ff87-130-209-252-154.ngrok-free.app"
# URL = f"wss://{NGROK_URL}/ws",
# Number of days to create challenges for

# ------------------------------------------------------

USER = "11AV"
DATA_FOLDER = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) + "/data"
N_TIMESTEP = 24
N_POSITION = 50
TIMESTEP = np.linspace(0, 1, N_TIMESTEP)
POSITION = np.linspace(0, 20000, N_POSITION)
SIGMA_POSITION_TRANSITION = 10.0
N_VELOCITY = 30
# velocity = np.concatenate((np.zeros(1), np.geomspace(2, np.max(combined)+1, n_velocity-1)))
VELOCITY = np.linspace(0, 12000, N_VELOCITY)
GENERATIVE_MODEL_PSEUDO_COUNT_JITTER = 1e-03
ACTIVE_INFERENCE_PSEUDO_COUNT_JITTER = 0.1
GAMMA = 1.0

# ------------------------------------------------------
# Parameters for the generative model
N_SAMPLES = 1000
CHILD_MODELS_N_COMPONENTS = 3
SEED_GENERATIVE_MODEL = 42
# ------------------------------------------------------
# Parameters for the assistant model
LOG_PRIOR = np.log(softmax(np.arange(N_POSITION)*2))
# Number of new instances of the (same) model
N_RESTART = 10
# Number of episodes to run this instance of model for
N_EPISODES = 200
# Seed
SEED_ASSISTANT = 42

# ------------------------------------------
# For the simulation
SEED_RUN = 42

# -------------------------------------------

HEURISTIC = None
N_DAY = N_EPISODES

# assert N_DAY > 1, "N_DAY must be greater than 1"

# _-------------------------------------

INIT_POS_IDX = np.absolute(POSITION).argmin()  # Something close to 0
INIT_V_IDX = np.absolute(VELOCITY).argmin()    # Something close to 0

# print ---------------------------------

LOG_AT_EACH_EPISODE = True
LOG_AT_EACH_TIMESTEP = False
