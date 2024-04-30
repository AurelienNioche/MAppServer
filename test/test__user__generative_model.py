import os

from test.assistant_model.action_plan_selection import \
    make_a_step

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from datetime import timedelta
import json
import numpy as np

from MAppServer.settings import TIME_ZONE
from user.models import User
from test.user_simulation import creation
from test.user_simulation import websocket_client
from test.generative_model.core import generative_model
from test.activity.activity import get_timestep, extract_actions

from assistant_model.action_plan_generation import get_possible_action_plans
from assistant_model.action_plan_generation import get_challenges

from test.config.config import (
    TIMESTEP, POSITION, VELOCITY, N_DAY, N_CHALLENGE, OFFER_WINDOW, OBJECTIVE, AMOUNT,
    BASE_CHEST_AMOUNT, USERNAME, INIT_STATE, EXPERIMENT_NAME, FIRST_CHALLENGE_OFFER,
    CHALLENGE_WINDOW, CHALLENGE_DURATION, STARTING_DATE, URL, NOW,
    USER, DATA_FOLDER, N_SAMPLES, CHILD_MODELS_N_COMPONENTS,
    GENERATIVE_MODEL_PSEUDO_COUNT_JITTER,
    SIGMA_POSITION_TRANSITION, SEED_GENERATIVE_MODEL, SEED_RUN,
    LOG_AT_EACH_TIMESTEP, LOG_AT_EACH_EPISODE
)


class FakeUser(websocket_client.DefaultUser):
    def __init__(self):
        super().__init__(username=USERNAME)
        self.timestep = TIMESTEP
        self.position = POSITION
        self.velocity = VELOCITY
        self.pos_idx = np.argmin(np.abs(self.position))  # Something close to 0
        self.v_idx = np.argmin(np.abs(self.velocity))  # Something close to 0

        self.n_steps = []

        challenges = get_challenges(
            start_time=FIRST_CHALLENGE_OFFER,
            time_zone=TIME_ZONE,
            challenge_window=CHALLENGE_WINDOW,
            offer_window=OFFER_WINDOW,
            n_challenges_per_day=N_CHALLENGE
        )
        self.action_plans = get_possible_action_plans(challenges=challenges, timestep=TIMESTEP)
        self.transition_velocity_atvv, self.transition_position_pvp = generative_model(
            action_plans=self.action_plans,
            user=USER, data_path=DATA_FOLDER,
            timestep=TIMESTEP, n_samples=N_SAMPLES,
            child_models_n_components=CHILD_MODELS_N_COMPONENTS,
            velocity=VELOCITY,
            pseudo_count_jitter=GENERATIVE_MODEL_PSEUDO_COUNT_JITTER,
            position=POSITION,
            sigma_transition_position=SIGMA_POSITION_TRANSITION,
            seed=SEED_GENERATIVE_MODEL
        )
        # np.save("action_plans_2.npy", action_plans)
        # np.save("timestep_2.npy", TIMESTEP)
        # np.save("position_2.npy", POSITION)
        # np.save("velocity_2.npy", VELOCITY)
        # np.save("transition_velocity_atvv_2.npy", self.transition_velocity_atvv)
        # np.save("transition_position_pvp_2.npy", self.transition_position_pvp)
        self._now = NOW
        self.starting_date = self._now.date()
        self.android_id = 0
        print("Seeding the random number generator with", SEED_RUN)
        self.rng = np.random.default_rng(seed=SEED_RUN)

        self.u = User.objects.filter(username=self.username).first()
        self.init_done = False

    def now(self):
        return self._now

    def update(self):
        # Extract variables
        position = self.position
        velocity = self.velocity
        timestep = self.timestep
        transition_velocity_atvv = self.transition_velocity_atvv
        transition_position_pvp = self.transition_position_pvp
        pos_idx = self.pos_idx
        v_idx = self.v_idx
        now = self.now()
        rng = self.rng
        # Get timestep index
        t_idx = get_timestep(now, timestep)
        if t_idx == 0 and not self.init_done:
            # steps = [{
            #         "ts": now.timestamp()*1000,
            #         "step_midnight": 0,
            #         "android_id": self.android_id
            #     }]
            # # print(f"Android ID {self.android_id} - Day {(self.now().date() - self.starting_date).days} - Timestep {t_idx} -  {step_midnight} steps done.")
            # self.android_id += 1
            steps = []
            to_return = {
                "now": now.strftime("%d/%m/%Y %H:%M:%S"),
                "steps": json.dumps(steps),
            }
            # Note to future self: action plan is not used here
            if LOG_AT_EACH_TIMESTEP:
                print("t_idx", t_idx, "a: NOT YET v_idx", v_idx, "pos_idx", pos_idx)
            # Note: we should NOT increment time here because we need an action plan for
            # transitioning to the next timestep
            self.init_done = True
            return to_return
        if t_idx >= timestep.size - 1:
            steps = []
            to_return = {
                "now": now.strftime("%d/%m/%Y %H:%M:%S"),
                "steps": json.dumps(steps),
                "skipAssistantUpdate": True
            }
            # Note to future self: action plan is not used here
            if LOG_AT_EACH_TIMESTEP:
                print("t_idx", t_idx, "a", 0, "v_idx", v_idx, "pos_idx", pos_idx, )
            self.increment_time()
            return to_return
        # Select action plan
        action_plan = extract_actions(
            u=self.u, timestep=timestep,
            now=now
        )
        # We mean a Markovian step
        action, new_v_idx, new_pos_idx = make_a_step(
            t_idx=t_idx, policy=action_plan,
            v_idx=v_idx, pos_idx=pos_idx,
            position=position, velocity=velocity,
            transition_velocity_atvv=transition_velocity_atvv,
            transition_position_pvp=transition_position_pvp,
            rng=rng
        )
        # Increment position and velocity
        self.v_idx = new_v_idx
        self.pos_idx = new_pos_idx
        # Increment time
        self.increment_time()
        steps = [{
                "ts": self.now().timestamp()*1000,  # equivalent of t_idx + 1
                "step_midnight": position[self.pos_idx],
                "android_id": self.android_id
        }]
        self.android_id += 1
        # if t_idx == 0:
        #     steps.insert(0, {
        #             "ts": now.timestamp()*1000,  # equivalent of t_idx
        #             "step_midnight": step_midnight,
        #             "android_id": self.android_id
        #         })
        #     # self.android_id += 1

        # print(f"Android ID {self.android_id} - Day {(self.now().date() - self.starting_date).days} - Timestep {t_idx} -  {step_midnight} steps done.")
        # self.android_id += 1
        to_return = {
            "now": now.strftime("%d/%m/%Y %H:%M:%S"),
            "steps": json.dumps(steps),
            "skipAssistantUpdate": True
        }
        return to_return

    def increment_time(self):
        new_now = self._now + timedelta(hours=1)
        if new_now > self.now().replace(hour=23, minute=59):
            n_days = (self.now().date() - self.starting_date).days

            ap = extract_actions(u=self.u, timestep=self.timestep, now=self.now())
            index = np.where((self.action_plans == ap).all(axis=1))[0][0]
            print(f"Day #{n_days}: {self.position[self.pos_idx]} steps done. Policy {index}")
            # difference = self.now() - datetime.combine(self.starting_date, time(), tzinfo=self.now().tzinfo)
            # print(f"day # {difference.days} - {self.position[self.pos_idx]} steps done.")
            new_now = new_now.replace(hour=0, minute=0)
            self.pos_idx = np.argmin(np.abs(self.position))  # Something close to 0
            self.v_idx = np.argmin(np.abs(self.velocity))
            self.init_done = False
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
    fake_user = FakeUser()
    websocket_client.run_bot(url=URL, user=fake_user)
    print("-" * 100)
    actions_taken = extract_actions(
        u=u, timestep=TIMESTEP)
    action_plans = get_possible_action_plans(
        challenges=u.challenge_set.order_by("dt_begin"),
        timestep=TIMESTEP
    )
    actions_taken = np.atleast_2d(actions_taken)
    for i, actions in enumerate(actions_taken):
        row_index = np.where((action_plans == actions).all(axis=1))[0][0]
        if LOG_AT_EACH_EPISODE:
            print(f"episode #{i} - policy: {row_index}")
    # for c in User.objects.filter(username=USERNAME).first().challenge_set.order_by("dt_begin"):
    #     print(c.dt_begin.astimezone(tz(TIME_ZONE)))


if __name__ == "__main__":
    main()
