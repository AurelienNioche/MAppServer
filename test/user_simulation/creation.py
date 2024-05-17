import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
from django.db import transaction
application = get_wsgi_application()

from datetime import datetime, timedelta
import uuid
import pytz

from MAppServer.settings import (
    TIME_ZONE,
    N_DAY,
    N_CHALLENGES_PER_DAY,
    OBJECTIVE,
    REWARD,
    INIT_STATE,
    CHALLENGE_WINDOW,
    CHALLENGE_DURATION,
    OFFER_WINDOW,
    BASE_CHEST_AMOUNT
)
from user.models import User, Challenge, Status


def generate_uuid():
    return str(uuid.uuid4())


@transaction.atomic
def create_test_user(
        starting_date: str,
        username: str,
        first_challenge_offer: int or float,
        experiment_name:  str,
        challenge_accepted=False):

    print("-" * 100)
    print("Test user creation")
    print("-" * 100)
    # --------------------------------------------------------------
    # Deal with dates and times

    starting_date = datetime.strptime(starting_date, "%d/%m/%Y")
    starting_date = pytz.timezone(TIME_ZONE).localize(starting_date)

    dt_first_challenge_offer = datetime.strptime(first_challenge_offer, "%H:%M")
    dt_first_challenge_offer = pytz.timezone(TIME_ZONE).localize(dt_first_challenge_offer)

    offer_window = timedelta(hours=OFFER_WINDOW)
    challenge_duration = timedelta(hours=CHALLENGE_DURATION)
    challenge_window = timedelta(hours=CHALLENGE_WINDOW)

    print("Starting date:", starting_date)
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
        base_chest_amount=BASE_CHEST_AMOUNT,
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
    for _ in range(N_DAY):
        current_time = dt_first_challenge_offer
        for ch_t in range(N_CHALLENGES_PER_DAY):

            dt_offer_begin = datetime(
                current_date.year, current_date.month, current_date.day,
                current_time.hour, current_time.minute, current_time.second, current_time.microsecond,
                current_date.tzinfo)

            print(f"Creating challenge for user {u.username} on {dt_offer_begin}.")

            # noinspection PyTypeChecker
            dt_offer_end = dt_earliest = dt_offer_begin + offer_window
            dt_begin = dt_offer_end
            dt_end = dt_begin + challenge_duration
            dt_latest = dt_earliest + challenge_window

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
                objective=OBJECTIVE,
                amount=REWARD,
                android_tag=random_uuid,
                server_tag=random_uuid,
                accepted=challenge_accepted,
            )

            current_time = dt_latest

        current_date += timedelta(days=1)

    print(f"Challenges successfully created for user {u.username}.")
    print("-" * 100)
    print("Test user creation completed successfully.")
    print("-" * 100)
    return u

