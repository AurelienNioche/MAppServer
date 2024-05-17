import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

import pytz
import tqdm
from datetime import timedelta
from pytz import timezone
import json
import numpy as np

from MAppServer.settings import (
    TIME_ZONE,
    POSITION, N_DAY,
    TEST_USERNAME, TEST_EXPERIMENT_NAME, TEST_FIRST_CHALLENGE_OFFER,
    TEST_STARTING_DATE, WEBSOCKET_URL, TEST_NOW,
    USER_FOR_GENERATIVE_MODEL, DATA_FOLDER, N_SAMPLES_FOR_GENERATIVE_MODEL, CHILD_MODELS_N_COMPONENTS,
    GENERATIVE_MODEL_PSEUDO_COUNT_JITTER, SEED_GENERATIVE_MODEL, TEST_SEED_RUN,
    LOG_AT_EACH_EPISODE,
    LOG_AT_EACH_TIMESTEP,
    INIT_POS_IDX,
    USE_PROGRESS_BAR
)
from user.models import User
from assistant.tasks import read_activities_and_extract_step_events
from core.action_plan_selection import make_a_step
from test.plot import plot
from test.user_simulation import creation, websocket_client
from test.generative_model.core import generative_model
from core.activity import extract_actions, step_events_to_cumulative_steps
from core.action_plan_generation import get_possible_action_plans, get_challenges
from core.timestep_and_datetime import get_timestep_from_datetime


class FakeUser(websocket_client.DefaultUser):
    def __init__(self):
        super().__init__(username=TEST_USERNAME)
        self.pos_idx = INIT_POS_IDX
        self.n_steps = []
        challenges = get_challenges(start_time=TEST_FIRST_CHALLENGE_OFFER)
        self.action_plans = get_possible_action_plans(challenges=challenges)
        self.transition = generative_model(
            action_plans=self.action_plans,
            user=USER_FOR_GENERATIVE_MODEL,
            data_path=DATA_FOLDER,
            n_samples=N_SAMPLES_FOR_GENERATIVE_MODEL,
            child_models_n_components=CHILD_MODELS_N_COMPONENTS,
            pseudo_count_jitter=GENERATIVE_MODEL_PSEUDO_COUNT_JITTER,
            seed=SEED_GENERATIVE_MODEL
        )
        self._now = TEST_NOW
        self.starting_date = self._now.date()
        self.android_id = 0
        self.rng = np.random.default_rng(seed=TEST_SEED_RUN)
        self.u = User.objects.filter(username=self.username).first()
        self.init_done = False
        if USE_PROGRESS_BAR:
            self.progress_bar = tqdm.tqdm(total=N_DAY, desc="Day progression")

    def now(self):
        return self._now.astimezone(timezone(TIME_ZONE))

    def update(self):
        # Extract variables
        transition = self.transition
        pos_idx = self.pos_idx
        now = self.now()
        rng = self.rng
        # Get timestep index
        t_idx = get_timestep_from_datetime(now)
        if t_idx == 0 and not self.init_done:
            to_return = {
                "now": now.strftime("%d/%m/%Y %H:%M:%S"),
                "steps": json.dumps([]),
            }
            self.init_done = True
            return to_return
        # Select action plan
        action_plan = extract_actions(u=self.u, now=now)
        # Log stuff
        # Compute the number of day
        n_days = (now.date() - self.starting_date).days
        if LOG_AT_EACH_EPISODE and t_idx == 0:
            # {self.position[self.pos_idx]} steps done.
            # noinspection PyUnresolvedReferences
            action_plan_idx = np.where((self.action_plans == action_plan).all(axis=1))[0][0]
            print("-" * 100)
            print(f"restart #0 - episode #{n_days} - policy #{action_plan_idx}")
            print("-" * 100)
        if USE_PROGRESS_BAR and t_idx == 0:
            self.progress_bar.update(1)
        # We mean a Markovian step
        action, new_pos_idx = make_a_step(
            t_idx=t_idx,
            policy=action_plan,
            pos_idx=pos_idx,
            transition=transition,
            rng=rng
        )
        # Increment position and velocity
        self.pos_idx = new_pos_idx
        # Increment time
        self.increment_time_and_reset_if_end_of_day()
        # Send the shite
        step_midnight = POSITION[new_pos_idx]
        # if LOG_AT_EACH_TIMESTEP:
        #     print(f"t_idx {t_idx:02} now", self.now(), "new_pos_idx", new_pos_idx, "n_steps", step_midnight)

        ts = self.to_timestamp(self.now())
        if t_idx == 23:
            ts -= 1000  # 1 second before midnight
        steps = [{
                "ts": ts,
                "step_midnight": step_midnight,
                "android_id": self.android_id
        }]
        self.android_id += 1
        to_return = {
            "now": self.now().strftime("%d/%m/%Y %H:%M:%S"),
            "steps": json.dumps(steps)
        }
        return to_return

    @staticmethod
    def to_timestamp(dt):
        return dt.astimezone(pytz.UTC).timestamp()*1000

    def increment_time_and_reset_if_end_of_day(self):
        end_of_day = self._now.replace(hour=23, minute=59, second=59, microsecond=999999)
        new_now = self._now + timedelta(hours=1)
        if new_now > end_of_day:
            new_now = new_now.replace(hour=0, minute=0, microsecond=0)
            self.pos_idx = INIT_POS_IDX
            self.init_done = False
        self._now = new_now

    def done(self):
        done = (self.now().date() - self.starting_date) >= timedelta(days=N_DAY)
        if USE_PROGRESS_BAR and done:
            self.progress_bar.close()
        return done


def run():

    creation.create_test_user(
        challenge_accepted=True,
        starting_date=TEST_STARTING_DATE,
        username=TEST_USERNAME,
        experiment_name=TEST_EXPERIMENT_NAME,
        first_challenge_offer=TEST_FIRST_CHALLENGE_OFFER
    )
    fake_user = FakeUser()
    websocket_client.run_bot(user=fake_user)


def plot_day_progression():

    u = User.objects.filter(username=TEST_USERNAME).first()
    step_events, _ = read_activities_and_extract_step_events(u=u)
    cum_steps = step_events_to_cumulative_steps(step_events=step_events)
    af_run = {
        "position": cum_steps
    }
    plot.plot_day_progression(af_run)


def main():

    run()
    plot_day_progression()


if __name__ == "__main__":
    main()

