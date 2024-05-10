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
NOW = datetime.now(timezone(TIME_ZONE)).replace(hour=0, minute=0, second=0, microsecond=0)

#     datetime.now(timezone(TIME_ZONE)).date(),
#     datetime.strptime(NOW_TIME, "%H:%M").time(),
#     tzinfo=timezone(TIME_ZONE)
# )
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
N_CHALLENGES_PER_DAY = 3
# NGROK_URL = "ff87-130-209-252-154.ngrok-free.app"
# URL = f"wss://{NGROK_URL}/ws",
# Number of days to create challenges for
# ------------------------------------------------------
USER = "11AV"
DATA_FOLDER = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) + "/data"
N_TIMESTEP = 24
TIMESTEP = np.linspace(0, 1, N_TIMESTEP)
N_POSITION = 100
POSITION = np.linspace(0, 40000, N_POSITION)
GENERATIVE_MODEL_PSEUDO_COUNT_JITTER = 1e-03
ACTIVE_INFERENCE_PSEUDO_COUNT_JITTER = 0.1
GAMMA = 1.0
# ------------------------------------------------------
# Parameters for the generative model
N_SAMPLES = 1000
CHILD_MODELS_N_COMPONENTS = 3
SEED_GENERATIVE_MODEL = 42
LOC_NUDGE_EFFECT = 10000
SCALE_NUDGE_EFFECT = 0.1
# ------------------------------------------------------
# Parameters for the assistant model
LOG_PRIOR = np.log(softmax(np.arange(N_POSITION)*2))
# Number of new instances of the (same) model
N_RESTART = 1
# Number of episodes to run this instance of model for
N_EPISODES = 10
# Seed
SEED_ASSISTANT = 42
# ------------------------------------------
# For the simulation
SEED_RUN = 42
# -------------------------------------------
HEURISTIC = None
N_DAY = N_EPISODES
# --------------------------------------
INIT_POS_IDX = np.absolute(POSITION).argmin()  # Something close to 0
# print ---------------------------------
LOG_AT_EACH_EPISODE = False
LOG_AT_EACH_TIMESTEP = False
LOG_PSEUDO_COUNT_UPDATE = False
LOG_ACTIVITY = False
LOG_ASSISTANT_MODEL = True
LOG_EXTRACT_STEP_EVENTS = False
LOG_WARNING_NAN = False
USE_PROGRESS_BAR = False
