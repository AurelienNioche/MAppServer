#%% Imports
import os

import \
    pytz

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

import tqdm
from datetime import timedelta
from pytz import timezone
import json
import numpy as np

from assistant.tasks import \
    read_activities_and_extract_step_events
from test.assistant_model.action_plan_selection import \
    make_a_step
from test.plot import \
    plot

from MAppServer.settings import TIME_ZONE
from user.models import User
from test.user_simulation import creation
from test.user_simulation import websocket_client
from test.generative_model.core import generative_model
from test.activity.activity import get_timestep, extract_actions, step_events_to_cumulative_steps
from test.assistant_model.action_plan_generation import get_possible_action_plans
from test.assistant_model.action_plan_generation import get_challenges

from test.config.config import (
    TIMESTEP, POSITION, N_DAY, N_CHALLENGES_PER_DAY, OFFER_WINDOW, OBJECTIVE, AMOUNT,
    BASE_CHEST_AMOUNT, USERNAME, INIT_STATE, EXPERIMENT_NAME, FIRST_CHALLENGE_OFFER,
    CHALLENGE_WINDOW, CHALLENGE_DURATION, STARTING_DATE, URL, NOW,
    USER, DATA_FOLDER, N_SAMPLES, CHILD_MODELS_N_COMPONENTS,
    GENERATIVE_MODEL_PSEUDO_COUNT_JITTER, SEED_GENERATIVE_MODEL, SEED_RUN,
    LOG_AT_EACH_EPISODE,
    LOG_PSEUDO_COUNT_UPDATE,
    INIT_POS_IDX
)


class FakeUser(websocket_client.DefaultUser):
    def __init__(self):
        super().__init__(username=USERNAME)
        self.timestep = TIMESTEP
        self.position = POSITION
        self.pos_idx = INIT_POS_IDX
        self.n_steps = []
        challenges = get_challenges(
            start_time=FIRST_CHALLENGE_OFFER,
            time_zone=TIME_ZONE,
            challenge_window=CHALLENGE_WINDOW,
            offer_window=OFFER_WINDOW,
            n_challenges_per_day=N_CHALLENGES_PER_DAY
        )
        self.action_plans = get_possible_action_plans(challenges=challenges, timestep=TIMESTEP)
        self.transition = generative_model(
            action_plans=self.action_plans,
            user=USER,
            data_path=DATA_FOLDER,
            timestep=TIMESTEP,
            n_samples=N_SAMPLES,
            child_models_n_components=CHILD_MODELS_N_COMPONENTS,
            pseudo_count_jitter=GENERATIVE_MODEL_PSEUDO_COUNT_JITTER,
            position=POSITION,
            seed=SEED_GENERATIVE_MODEL
        )
        # np.save("action_plans_2.npy", action_plans)
        # np.save("timestep_2.npy", TIMESTEP)
        # np.save("position_2.npy", POSITION)
        # np.save("velocity_2.npy", VELOCITY)
        # np.save("transition_velocity_atvv_2.npy", self.transition_velocity_atvv)
        # np.save("transition_position_pvp_2.npy", self.transition_position_pvp)
        self._now = NOW
        print("init now", self._now, self._now.tzinfo)
        self.starting_date = self._now.date()
        self.android_id = 0
        self.rng = np.random.default_rng(seed=SEED_RUN)
        self.u = User.objects.filter(username=self.username).first()
        self.init_done = False
        self.progress_bar = tqdm.tqdm(total=N_DAY, desc="Day progression")

    def now(self):
        return self._now.astimezone(timezone(TIME_ZONE))

    def update(self):
        # Extract variables
        position = self.position
        timestep = self.timestep
        transition = self.transition
        pos_idx = self.pos_idx
        now = self.now()
        rng = self.rng
        # Get timestep index
        t_idx = get_timestep(now, timestep)
        if t_idx == 0 and not self.init_done:
            to_return = {
                "now": now.strftime("%d/%m/%Y %H:%M:%S"),
                "steps": json.dumps([]),
            }
            self.init_done = True
            return to_return
        # if t_idx >= timestep.size - 1:
        #     steps = []
        #     to_return = {
        #         "now": now.strftime("%d/%m/%Y %H:%M:%S"),
        #         "steps": json.dumps(steps),
        #         "skipAssistantUpdate": True
        #     }
        #     # Note to future self: action plan is not used here
        #     # if LOG_AT_EACH_TIMESTEP:
        #     #    print("t_idx", t_idx, "a", 0, "v_idx", v_idx, "pos_idx", pos_idx, )
        #     self.increment_time()
        #     return to_return
        # Select action plan
        action_plan = extract_actions(
            u=self.u, timestep=timestep,
            now=now
        )
        # Log stuff
        # Compute the number of day
        n_days = (now.date() - self.starting_date).days
        if LOG_AT_EACH_EPISODE and t_idx == 0:
            # {self.position[self.pos_idx]} steps done.
            action_plan_idx = np.where((self.action_plans == action_plan).all(axis=1))[0][0]
            print("-" * 100)
            print(f"restart #0 - episode #{n_days} - policy #{action_plan_idx}")
            print("-" * 100)
        if t_idx == 0:
            self.progress_bar.update(1)
        # We mean a Markovian step
        action, new_pos_idx = make_a_step(
            t_idx=t_idx,
            policy=action_plan,
            pos_idx=pos_idx,
            position=position,
            transition=transition,
            rng=rng
        )
        # Increment position and velocity
        self.pos_idx = new_pos_idx
        # Increment time
        self.increment_time_and_reset_if_end_of_day()
        # Send the shite
        step_midnight = position[new_pos_idx]
        print("t_idx", t_idx, "now", self.now(), "new_pos_idx", new_pos_idx, "n_steps", step_midnight)

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
            "now": now.strftime("%d/%m/%Y %H:%M:%S"),
            "steps": json.dumps(steps),
            "skipAssistantUpdate": True
        }
        return to_return

    @staticmethod
    def to_timestamp(dt):
        return dt.astimezone(pytz.UTC).timestamp()*1000

    def increment_time_and_reset_if_end_of_day(self):
        new_now = self._now + timedelta(hours=1)
        if new_now > self.now().replace(hour=23, minute=59):
            # difference = self.now() - datetime.combine(self.starting_date, time(), tzinfo=self.now().tzinfo)
            # print(f"day # {difference.days} - {self.position[self.pos_idx]} steps done.")
            new_now = new_now.replace(hour=0, minute=0)
            self.pos_idx = np.argmin(np.abs(self.position))  # Something close to 0
            self.init_done = False
            # print("-" * 100)
        self._now = new_now

    def done(self):
        done = (self.now().date() - self.starting_date) >= timedelta(days=N_DAY)
        if done:
            self.progress_bar.close()
        return done


def run():

    creation.create_test_user(
        challenge_accepted=True,
        starting_date=STARTING_DATE,
        n_day=N_DAY,
        n_challenge=N_CHALLENGES_PER_DAY,
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
    fake_user = FakeUser()
    websocket_client.run_bot(url=URL, user=fake_user)


def plot_day_progression():

    u = User.objects.filter(username=USERNAME).first()
    step_events, dates, dt_min, dt_max = read_activities_and_extract_step_events(u=u)
    print(dates)
    cum_steps = step_events_to_cumulative_steps(
        step_events=step_events,
        timestep=TIMESTEP
    )
    af_run = {
        "position": cum_steps
    }
    plot.plot_day_progression(af_run)


def main():

    run()
    plot_day_progression()


if __name__ == "__main__":
    main()

