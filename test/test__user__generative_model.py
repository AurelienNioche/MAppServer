import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from datetime import datetime, timedelta, time
from pytz import timezone as tz
import json
import numpy as np

from MAppServer.settings import TIME_ZONE
from user.models import User
from test.user_simulation import creation
from test.user_simulation import websocket_client
from test.generative_model.core import generative_model
from test.activity.activity import get_timestep, is_nudged, extract_actions

from assistant_model.action_plan_generation import get_possible_action_plans
from assistant_model.action_plan_generation import get_challenges

from test.config.config import (
    TIMESTEP, POSITION, VELOCITY, N_DAY, N_CHALLENGE, OFFER_WINDOW, OBJECTIVE, AMOUNT,
    BASE_CHEST_AMOUNT, USERNAME, INIT_STATE, EXPERIMENT_NAME, FIRST_CHALLENGE_OFFER,
    CHALLENGE_WINDOW, CHALLENGE_DURATION, STARTING_DATE, URL, _now, _now_time,
    USER, DATA_FOLDER, N_SAMPLES, CHILD_MODELS_N_COMPONENTS, PSEUDO_COUNT_JITTER,
    SIGMA_POSITION_TRANSITION
)


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

        challenges = get_challenges(
            time_zone=TIME_ZONE,
            challenge_window=CHALLENGE_WINDOW,
            offer_window=OFFER_WINDOW,
            n_challenges_per_day=N_CHALLENGE,
        )
        self.action_plans = get_possible_action_plans(challenges=challenges, timestep=TIMESTEP)
        self.transition_velocity_atvv, self.transition_position_pvp = generative_model(
            action_plans=self.action_plans,
            user=USER, data_path=DATA_FOLDER,
            timestep=TIMESTEP, n_samples=N_SAMPLES,
            child_models_n_components=CHILD_MODELS_N_COMPONENTS,
            velocity=VELOCITY, pseudo_count_jitter=PSEUDO_COUNT_JITTER,
            position=POSITION, sigma_transition_position=SIGMA_POSITION_TRANSITION
        )

        self._now = datetime.combine(
            date=_now.date(), time=_now_time,
            tzinfo=tz(TIME_ZONE))

        self.starting_date = _now.date()
        self.android_id = 0

    def now(self):
        return self._now

    def update(self):
        position = self.position
        velocity = self.velocity
        timestep = self.timestep
        transition_velocity_atvv = self.transition_velocity_atvv
        transition_position_pvp = self.transition_position_pvp
        pos_idx = self.pos_idx
        v_idx = self.v_idx
        now = self.now()
        username = self.username

        t_idx = get_timestep(now, timestep)
        if t_idx >= timestep.size - 1:
            self.increment_time()
            steps = []
            to_return = {
                "now": now.strftime("%d/%m/%Y %H:%M:%S"),
                "steps": json.dumps(steps),
            }
            return to_return

        a = int(is_nudged(now=now, username=username))

        # Draw new velocity
        p = transition_velocity_atvv[a, t_idx, v_idx, :]
        new_v_idx = np.random.choice(np.arange(velocity.size), p=p)

        # Update velocity and position
        v_idx = new_v_idx
        p = transition_position_pvp[pos_idx, v_idx, :]
        pos_idx = np.random.choice(
            position.size,
            p=p)

        step_midnight = position[pos_idx]

        # Update time
        self.increment_time()
        self.v_idx = v_idx
        self.pos_idx = pos_idx

        steps = [{
                "ts": now.timestamp()*1000,
                "step_midnight": step_midnight,
                "android_id": self.android_id
            }]
        # print(f"Android ID {self.android_id} - Day {(self.now().date() - self.starting_date).days} - Timestep {t_idx} -  {step_midnight} steps done.")
        self.android_id += 1
        to_return = {
            "now": self.now().strftime("%d/%m/%Y %H:%M:%S"),
            "steps": json.dumps(steps),
        }

        return to_return

    def increment_time(self):
        new_now = self._now + timedelta(hours=1)
        if new_now > self.now().replace(hour=23, minute=59):
            difference = self.now() - datetime.combine(self.starting_date, time(), tzinfo=self.now().tzinfo)
            # print(f"day # {difference.days} - {self.position[self.pos_idx]} steps done.")
            new_now = new_now.replace(hour=0, minute=0)
            self.pos_idx = np.argmin(np.abs(self.position))  # Something close to 0
            self.v_idx = np.argmin(np.abs(self.velocity))
            # print("-" * 100)
        self._now = new_now

    def done(self):
        return (self.now().date() - self.starting_date) >= timedelta(days=N_DAY)


def main():

    u = creation.create_test_user(
        challenge_accepted=True,
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

    print("-" * 100)

    actions_taken = extract_actions(
        u=u, timestep=TIMESTEP)
    for i, actions in enumerate(actions_taken):
        print(f"Day #{i}:", actions)

    for c in User.objects.filter(username=USERNAME).first().challenge_set.order_by("dt_begin"):
        print(c.dt_begin.astimezone(tz(TIME_ZONE)))


if __name__ == "__main__":
    main()
