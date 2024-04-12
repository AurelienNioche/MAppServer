import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
from django.db import transaction

application = get_wsgi_application()

from MAppServer.settings import TIME_ZONE

import json
import websocket
from datetime import datetime, timedelta
import uuid
import pytz

from MAppServer.settings import APP_VERSION
from user.models import User, Activity, Challenge, Status


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
NOW = datetime.combine(date=_now.date(), time=_now_time,
                       tzinfo=pytz.timezone(TIME_ZONE)).strftime("%d/%m/%Y %H:%M:%S")
# Experiment name (can be anything)
EXPERIMENT_NAME = "not-even-an-alpha-test"
# Amount of money already in the chest
base_chest_amount = 6
objective = 10
# Amount of reward (in pounds) for each challenge completed
amount = 0.4
# Number of days to create challenges for
n_day = 1
offer_window = timedelta(minutes=15)
CHALLENGE_WINDOW = timedelta(hours=3)
CHALLENGE_DURATION = timedelta(hours=1)
n_challenge = 3


# NGROK_URL = "ff87-130-209-252-154.ngrok-free.app"
# URL = f"wss://{NGROK_URL}/ws",


def generate_uuid():
    return str(uuid.uuid4())


@transaction.atomic
def create_test_user():

    print("TEST USER CREATION")

    # --------------------------------------------------------------
    # Deal with dates and times

    starting_date = datetime.strptime(STARTING_DATE, "%d/%m/%Y")
    starting_date = pytz.timezone(TIME_ZONE).localize(starting_date)

    dt_first_challenge_offer = datetime.strptime(FIRST_CHALLENGE_OFFER, "%H:%M")
    dt_first_challenge_offer = pytz.timezone(TIME_ZONE).localize(dt_first_challenge_offer)

    print("starting date:", starting_date)
    # ---------------------------------------------------------------

    u = User.objects.filter(username=USERNAME).first()
    if u is not None:
        u.delete()
        print("User deleted.")
        print("-" * 20)

    u = User.objects.create_user(
        username=USERNAME,
        experiment=EXPERIMENT_NAME,
        starting_date=starting_date,
        base_chest_amount=base_chest_amount,
    )

    if u is not None:
        print(f"User {u.username} successfully created.")
        print("-" * 20)
    else:
        raise ValueError("Something went wrong! User not created.")

    s = Status.objects.create(user=u, state=INIT_STATE)
    if s is not None:
        print(f"Status successfully created for user {u.username}.")
        print("-" * 20)
    else:
        raise ValueError("Something went wrong! Status not created")

    # ---------------------------------------------------------------
    # Create challenges

    current_date = starting_date
    dt_end = None
    for _ in range(n_day):
        current_time = dt_first_challenge_offer
        for ch_t in range(n_challenge):

            dt_offer_begin = datetime(
                current_date.year, current_date.month, current_date.day,
                current_time.hour, current_time.minute, current_time.second, current_time.microsecond,
                current_date.tzinfo)

            print(f"Creating challenge for user {u.username} on {dt_offer_begin}.")

            # noinspection PyTypeChecker
            dt_offer_end = dt_earliest = dt_offer_begin + offer_window
            dt_begin = dt_offer_end
            dt_end = dt_begin + CHALLENGE_DURATION
            dt_latest = dt_earliest + CHALLENGE_WINDOW

            random_uuid = generate_uuid()

            Challenge.objects.create(
                user=u,
                dt_offer_begin=dt_offer_begin,
                dt_offer_end=dt_offer_end,
                # Earliest time the challenge could be active is the end of the offer window
                dt_earliest=dt_earliest,
                dt_latest=dt_latest,
                dt_begin=dt_begin,
                dt_end=dt_end,
                objective=objective,
                amount=amount,
                android_tag=random_uuid,
                server_tag=random_uuid)

            current_time = dt_latest

        current_date += timedelta(days=1)

    print(f"Challenges successfully created for user {u.username}.")
    print(f"Last challenge ends at: {dt_end}.")
    print("-" * 20)
    print("Test user creation completed successfully.")


def generate_fake_steps(
        sec_delta_between_steps=60**2, step_delta_between_steps=20, n=10,
        base_step=10, base_sec=0
) -> list[dict]:
    step_events = []
    now = datetime.strptime(NOW, "%d/%m/%Y %H:%M:%S")
    for i in range(n):
        step_events.append(
            {
                "ts": (now.timestamp() - base_sec - i*sec_delta_between_steps)*1000,
                "step_midnight": base_step + step_delta_between_steps*i,
                "android_id": i
            }
        )
    return step_events


def generate_unsynced_challenges() -> list[dict]:
    return []


def generate_status():

    return User.objects.filter(username=USERNAME).first().status_set.first().to_android_dict()


class Bot(websocket.WebSocketApp):
    """
    ws://192.168.0.14:8080/ws
    wss://samoa.dcs.gla.ac.uk/mapp/ws
    """

    def __init__(
        self,
        waiting_time=2,
    ):
        super().__init__(
            URL,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )

        self.username = USERNAME

        # Websocket parameters
        self.waiting_time = waiting_time

    @staticmethod
    def on_message(ws, json_string):
        print(f"I received: {json_string}")
        msg = json.loads(json_string)
        subject = msg["subject"]
        f = getattr(ws, f"after_{subject}")
        f(msg)

    @staticmethod
    def on_error(ws, error):
        print(f"I got error: {error}")

    @staticmethod
    def on_close(ws, close_status_code, close_msg):
        print(f"I'm closing.")
        if close_status_code or close_msg:
            print(f"Close status code: {close_status_code}")
            print(f"Close message: {close_msg}")

    @staticmethod
    def on_open(ws):
        print("I'm open.")
        ws.login()

    def send_message(self, message):
        string_msg = json.dumps(message, indent=4)
        print(f"I'm sending: {string_msg}")
        self.send(string_msg)

    def login(self):
        message = {
            "subject": "login",
            "appVersion": APP_VERSION,
            "username": self.username,
            "resetUser": False,
        }
        self.send_message(message)

    def after_login(self, msg):
        print("After login: giving a fake update")
        assert msg["ok"]
        # Give a fake activity update
        self.update()

    def update(self):
        message = {
            "subject": "update",
            "appVersion": APP_VERSION,
            "username": self.username,
            "now": NOW,  # For testing purposes
            "steps": json.dumps(generate_fake_steps()),
            "status": json.dumps(generate_status()),
            "interactions": json.dumps([]),
            "unSyncedChallenges": json.dumps(generate_unsynced_challenges()),
        }
        self.send_message(message)

    def after_update(self, msg):
        print("Update done, test successful!")
        self.close()


def main():

    # # reset the user
    # u = User.objects.filter(username=USERNAME).first()
    # if u is not None:
    #     # Delete all the activities
    #     Activity.objects.filter(user=u).delete()

    create_test_user()

    websocket.enableTrace(True)
    ws = Bot()
    ws.run_forever()


if __name__ == "__main__":
    # from test_user__create import test_user__create
    # test_user__create()
    main()
