import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from django.db import transaction
import pytz
from datetime import datetime, timedelta, time

from user.models import User, Challenge, Status
from MAppServer.settings import TIME_ZONE

import uuid


INIT_STATE = "experimentNotStarted"


def generate_uuid():
    return str(uuid.uuid4())


@transaction.atomic
def create_test_user():

    first_challenge_offer = "07:30"
    # Username (can be anything)
    username = "123test"
    # Starting date of the experiment
    starting_date = "28/03/2024"
    # Experiment name (can be anything)
    experiment_name = "not-even-an-alpha-test"
    # Amount of money already in the chest
    base_chest_amount = 6
    objective = 10
    # Amount of reward (in pounds) for each challenge completed
    amount = 0.4
    # Number of days to create challenges for
    n_day = 2
    offer_window = timedelta(minutes=30)
    challenge_window = timedelta(hours=4)
    n_challenge = 3

    print("BASIC TEST USER CREATION")

    # --------------------------------------------------------------
    # Deal with dates and times

    starting_date = datetime.strptime(starting_date, "%d/%m/%Y")
    starting_date = pytz.timezone(TIME_ZONE).localize(starting_date)

    dt_first_challenge_offer = datetime.strptime(first_challenge_offer, "%H:%M")
    dt_first_challenge_offer = pytz.timezone(TIME_ZONE).localize(dt_first_challenge_offer)

    print(starting_date)
    # ---------------------------------------------------------------

    u = User.objects.filter(username=username).first()
    if u is not None:
        u.delete()
        print("User deleted.")
        print("-" * 20)

    u = User.objects.create_user(
        username=username,
        experiment=experiment_name,
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
    for _ in range(n_day):
        current_time = dt_first_challenge_offer
        for ch_t in range(n_challenge):

            dt_offer_begin = datetime(
                current_date.year, current_date.month, current_date.day,
                current_time.hour, current_time.minute, current_time.second, current_time.microsecond,
                current_date.tzinfo)

            # noinspection PyTypeChecker
            dt_offer_end = dt_offer_begin + offer_window
            dt_begin = dt_offer_end
            dt_end = dt_begin + challenge_window

            random_uuid = generate_uuid()

            Challenge.objects.create(
                user=u,
                dt_offer_begin=dt_offer_begin,
                dt_offer_end=dt_offer_end,
                dt_begin=dt_begin,
                dt_end=dt_end,
                objective=objective,
                amount=amount,
                android_tag=random_uuid,
                server_tag=random_uuid)

            current_time = dt_end

        current_date += timedelta(days=1)

    print(f"Challenges successfully created for user {u.username}.")
    print("-" * 20)
    print("Test user creation completed successfully.")


if __name__ == "__main__":
    create_test_user()
