import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from datetime import datetime, timedelta
import pytz

from MAppServer.settings import TIME_ZONE
from test.user_simulation import creation
from test.user_simulation import websocket_client


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
                       tzinfo=pytz.timezone(TIME_ZONE))
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

    websocket_client.run_bot(url=URL, username=USERNAME)


if __name__ == "__main__":
    main()
