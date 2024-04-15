import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from datetime import datetime, timedelta
import pytz
import json
import numpy as np
from scipy.special import softmax

from MAppServer.settings import TIME_ZONE
from user.models import User
from test.user_simulation import creation
from test.user_simulation import websocket_client
from test.generative_model.core import generative_model

from assistant.tasks import get_timestep


URL = "ws://127.0.0.1:8080/ws"
USERNAME = "123test"
INIT_STATE = "experimentNotStarted"
# WHen things will start
FIRST_CHALLENGE_OFFER = "7:30"
# Define "now" for debug purposes
NOW_TIME = "7:00"
_now = datetime.now()
_now_time = datetime.strptime(NOW_TIME, "%H:%M").time()
# Starting date of the experiment
STARTING_DATE = _now.date().strftime("%d/%m/%Y")  # "28/03/2024"
# Experiment name (can be anything)
EXPERIMENT_NAME = "not-even-an-alpha-test"
# Amount of money already in the chest
BASE_CHEST_AMOUNT = 6
OBJECTIVE = 10
# Amount of reward (in pounds) for each challenge completed
AMOUNT = 0.4
# Number of days to create challenges for
N_DAY = 1
OFFER_WINDOW = timedelta(minutes=15)
CHALLENGE_WINDOW = timedelta(hours=3)
CHALLENGE_DURATION = timedelta(hours=1)
N_CHALLENGE = 3
# NGROK_URL = "ff87-130-209-252-154.ngrok-free.app"
# URL = f"wss://{NGROK_URL}/ws",

# ------------------------------------------------------

USER = "11AV"
DATA_FOLDER = data_path = os.path.dirname(os.path.dirname(__file__)) + "/data"
N_TIMESTEP = 11
N_POSITION = 60
TIMESTEP = np.linspace(0, 1, N_TIMESTEP)
POSITION = np.linspace(0, 20000, N_POSITION)
SIGMA_POSITION_TRANSITION = 10.0
N_VELOCITY = 60
# velocity = np.concatenate((np.zeros(1), np.geomspace(2, np.max(combined)+1, n_velocity-1)))
VELOCITY = np.linspace(0, 15000+1, N_VELOCITY)
PSEUDO_COUNT_JITTER = 1e-3

N_SAMPLES = 1000
CHILD_MODELS_N_COMPONENTS = 3
LOG_PRIOR = np.log(softmax(np.arange(N_POSITION)*2))
N_RESTART = 4
N_EPISODES = 200


# def position_to_idx(position):
#     return np.argmin(np.abs(POSITION - position))


def extract_actions(now, username):
    user = User.objects.filter(username=username).first()
    # actions = np.zeros((deriv_cum_steps.shape[0], N_TIMESTEP), dtype=int)
    ch = u.challenge_set.filter(accepted=True, dt_end__lt=now)  # Less than now
    ch_date = np.asarray([dates.index(ch.dt_begin.date()) for ch in ch])
    ch_timestep = np.asarray([get_timestep(ch.dt_begin) for ch in ch])
    for a, t in zip(ch_date, ch_timestep):
        actions[a, t] = 1


class FakeUser(websocket_client.DefaultUser):
    def __init__(self,
                 timestep=TIMESTEP,
                 position=POSITION,
                 velocity=VELOCITY,
                 _now=_now, _now_time=_now_time):
        super().__init__(username=USERNAME)
        self.timestep = timestep
        self.position = position
        self.velocity = velocity
        self.pos_idx = np.argmin(np.abs(self.position))  # Something close to 0
        self.v_idx = np.argmin(np.abs(self.velocity))  # Something close to 0
        self.transition_velocity_atvv, self.transition_position_pvp, self.action_plans = generative_model(
            user=USER, data_path=DATA_FOLDER,
            timestep=TIMESTEP, n_samples=N_SAMPLES,
            child_models_n_components=CHILD_MODELS_N_COMPONENTS,
            velocity=VELOCITY, pseudo_count_jitter=PSEUDO_COUNT_JITTER,
            position=POSITION, sigma_transition_position=SIGMA_POSITION_TRANSITION
        )

        self._now = datetime.combine(
            date=_now.date(), time=_now_time,
            tzinfo=pytz.timezone(TIME_ZONE))

    def now(self):
        return self._now

    def steps(self):
        return [
            {
                "ts": (self.now() - timedelta(minutes=30)).timestamp()*1000,
                "step_midnight": 1,
                "android_id": 0
            },
            {
                "ts": (self.now() - timedelta(minutes=20)).timestamp()*1000,
                "step_midnight": 2,
                "android_id": 1
            },
            {
                "ts": (self.now() - timedelta(minutes=10)).timestamp()*1000,
                "step_midnight": 3,
                "android_id": 2
            }
        ]

    def update(self):
        position = self.position
        velocity = self.velocity
        timestep = self.timestep
        transition_velocity_atvv = self.transition_velocity_atvv
        transition_position_pvp = self.transition_position_pvp
        pos_idx = self.pos_idx
        v_idx = self.v_idx

        t_idx = get_timestep(self.now(), timestep)

        a = extract_action(now, username)

        # Draw new velocity
        new_v_idx = np.random.choice(
            np.arange(velocity.size),
            p=transition_velocity_atvv[a, t_idx, v_idx, :])

        # Update velocity and position
        v_idx = new_v_idx
        pos_idx = np.random.choice(
            position.size,
            p=transition_position_pvp[pos_idx, v_idx, :])

        step_midnight = position[pos_idx]

        # Update time
        self._now += timedelta(minutes=24*60/timestep.size)

        steps = [{
                "ts": (self.now() - timedelta(minutes=20)).timestamp()*1000,
                "step_midnight": step_midnight,
                "android_id": 1
            }]

        to_return = {
            "now": self.now().strftime("%d/%m/%Y %H:%M:%S"),
            "steps": json.dumps(steps),
        }

        return to_return


def main():

    creation.create_test_user(
        starting_date=STARTING_DATE,
        n_day=N_DAY,
        n_challenge=N_CHALLENGE,
        offer_window=OFFER_WINDOW,
        objective=OBJECTIVE,
        amount=AMOUNT,
        base_chest_amount=BASE_CHEST_AMOUNT,
        username=USERNAME,
        init_state=INIT_STATE,
        experiment_name=EXPERIMENT_NAME,
        first_challenge_offer=FIRST_CHALLENGE_OFFER,
        challenge_window=CHALLENGE_WINDOW,
        challenge_duration=CHALLENGE_DURATION
    )

    websocket_client.run_bot(url=URL, user=FakeUser())


if __name__ == "__main__":
    main()
