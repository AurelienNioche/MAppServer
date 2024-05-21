"""Django's settings for the MAppServer project, and config for the experiment."""
import os
import sys
from datetime import datetime
from pytz import timezone
import numpy as np
from scipy.special import softmax
from django.conf.locale.en import formats as en_formats

from . credentials import SECRET_KEY, DB_NAME, DB_PASSWORD, DB_USER, \
    EMAIL_HOST_USER, EMAIL_HOST_PASSWORD

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATETIME_FORMAT = 'Y-m-d H:i:s'
DEBUG = True
ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "*"
]
# Application definition
INSTALLED_APPS = [
    'user.apps.UserConfig',
    'assistant.apps.AssistantConfig',
     # 'django_celery_beat',
    'reception_desk.apps.ReceptionDeskConfig',
    'channels',
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]
# noinspection PyUnresolvedReferences
MIDDLEWARE = [
    'MAppServer.middleware.TimezoneMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
# noinspection PyUnresolvedReferences
ROOT_URLCONF = 'MAppServer.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
WSGI_APPLICATION = "MAppServer.wsgi.application"
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': 'localhost',
        'PORT': '5432'
    },
}
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/
LANGUAGE_CODE = 'en-gb'
TIME_ZONE = 'Europe/London'
USE_I18N = False
USE_L10N = False
USE_TZ = True
STATIC_URL = '/mapp/static/'
# noinspection PyUnresolvedReferences
STATIC_ROOT = os.path.join(BASE_DIR, "static/")
ASGI_APPLICATION = 'MAppServer.asgi.application'
AUTH_USER_MODEL = 'user.User'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
APP_VERSION = "2023.08.08"
SERVER_RELATIVE_BASE_DIR = "DjangoApps/MAppServer"
SERVER_BASE_DIR = os.path.expanduser(f"~/{SERVER_RELATIVE_BASE_DIR}")
SERVER_DATA_DIR = f"{SERVER_BASE_DIR}/data"
SERVER_USER = "aurelien"
SERVER_DOMAIN = "pearse.dcs.gla.ac.uk"
DATA_FOLDER = "data"
LATEST_DUMP_FOLDER = f"dump_latest"
USER_CREATION_CSV_PATH = f"{DATA_FOLDER}/user_creation"
SERVER_LATEST_DUMP_PATH = f"{SERVER_BASE_DIR}/{DATA_FOLDER}/{LATEST_DUMP_FOLDER}"
SERVER_LATEST_DUMP_RELATIVE_PATH = f"{SERVER_RELATIVE_BASE_DIR}/{DATA_FOLDER}/{LATEST_DUMP_FOLDER}"
DOWNLOAD_FOLDER = f"{DATA_FOLDER}/{LATEST_DUMP_FOLDER}"
DOWNLOAD_FOLDER_ABSOLUTE_PATH = f"{BASE_DIR}/{DATA_FOLDER}/{LATEST_DUMP_FOLDER}"
CSRF_TRUSTED_ORIGINS = [
    f"https://{SERVER_DOMAIN}",
    "https://*.ngrok-free.app",
    "https://localhost:8080"]
# ----------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------
if os.sys.platform == "darwin":
    WEBSOCKET_URL = "ws://127.0.0.1:8080/ws"
else:
    WEBSOCKET_URL = "wss://samoa.dcs.gla.ac.uk/mapp/ws"
#
# "wss://samoa.dcs.gla.ac.uk/mapp/ws"  # "wss://ea4e-130-209-252-154.ngrok-free.app/ws"    # "ws://127.0.0.1:8080/ws"
# -------------------------------------------------------------------------------------------------------------------
# WHen things will start
TEST_FIRST_CHALLENGE_OFFER = "7:00"
# Define "now" for debug purposes
TEST_NOW = datetime.now(timezone(TIME_ZONE)).replace(hour=0, minute=0, second=0, microsecond=0)
# Starting date of the experiment
TEST_STARTING_DATE = TEST_NOW.date().strftime("%d/%m/%Y")  # "28/03/2024"
# Experiment name (can be anything)
TEST_USERNAME = "123test"
TEST_EXPERIMENT_NAME = "not-even-an-alpha-test"
# Number of new instances of the (same) model
TEST_N_RESTART = 1
# Number of episodes to run this instance of model for
TEST_SEED_RUN = 42
# ------------------------------------------------------
# ------------------------------------------------------
# Experiment parameters --------------------------------
# Amount of money already in the chest
BASE_CHEST_AMOUNT = 6
# Money amount per challenge
REWARD = 0.5
OBJECTIVE = 10
# Amount of reward (in pounds) for each challenge completed
AMOUNT = 3
OFFER_WINDOW = 1           # in hours  #TODO: Change to 2
CHALLENGE_WINDOW = 2      # in hours   #TODO: Change to 12
CHALLENGE_DURATION = 1     # in hours  #TODO: Change to 3
N_CHALLENGES_PER_DAY = 1               #TODO: Change to 1
DISCARD_OVERLAPPING_STRATEGIES = True
N_DAY = 30
N_TIMESTEP = 24
TIMESTEP = np.linspace(0, 1, N_TIMESTEP)
N_POSITION = 10
POSITION = np.linspace(0, 15000, N_POSITION)
# ------------------------------------------------------
# Parameters for the assistant model
ACTIVE_INFERENCE_PSEUDO_COUNT_JITTER = 0.3
GAMMA = 1.0
LOG_PRIOR = np.log(softmax(np.arange(N_POSITION)*2))
SEED_ASSISTANT = 40
# ------------------------------------------------------
# Parameters for the generative model
DATA_FOLDER = os.path.dirname(os.path.dirname(__file__)) + "/data"
USER_FOR_GENERATIVE_MODEL = "11AV"
GENERATIVE_MODEL_PSEUDO_COUNT_JITTER = 1e-03
N_SAMPLES_FOR_GENERATIVE_MODEL = 1000
CHILD_MODELS_N_COMPONENTS = 3
SEED_GENERATIVE_MODEL = 42
LOC_NUDGE_EFFECT = 1000
SCALE_NUDGE_EFFECT = 50
# -------------------------------------------
# Using an heuristic to debug
HEURISTIC = None
# For the simulation -----------------------------
INIT_POS_IDX = np.absolute(POSITION).argmin()  # Something close to 0
# Formatting parameters -------------------------------------------
FORMAT = '%Y-%m-%d %H:%M:%S.%f'
FORMAT_DATE = '%Y-%m-%d'
# ----------------------------------
# Other constants
INIT_STATE = "experimentNotStarted"
# ----------------------------------------
# For the logs ---------------------------------
LOG_DIR = "logs"
FILE_LOGGING = True
LOG_AT_EACH_EPISODE = False
LOG_AT_EACH_TIMESTEP = False
LOG_PSEUDO_COUNT_UPDATE = False
LOG_ACTIVITY = False
LOG_ASSISTANT_MODEL = True
LOG_EXTRACT_STEP_EVENTS = False
LOG_WARNING_NAN = False
USE_PROGRESS_BAR = False
# -----------------------------------------
assert CHALLENGE_WINDOW % CHALLENGE_DURATION == 0, "Mmmh, that's not really working, is it?"
