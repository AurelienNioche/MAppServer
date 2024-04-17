import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
from django.db import transaction
application = get_wsgi_application()

from datetime import datetime, timedelta
import uuid
import pytz

from MAppServer.settings import TIME_ZONE
from user.models import User, Challenge, Status


def generate_uuid():
    return str(uuid.uuid4())


@transaction.atomic
def create_test_user(
        starting_date: str,
        n_day: int,
        n_challenge: int,
        objective: int or float,
        amount: int or float,
        base_chest_amount: int or float,
        username: str,
        init_state: str,
        experiment_name:  str,
        first_challenge_offer: str,
        offer_window: int or float,
        challenge_window: int or float,
        challenge_duration: int or float,
        challenge_accepted=False):

    print("Test user creation")

    # --------------------------------------------------------------
    # Deal with dates and times

    starting_date = datetime.strptime(starting_date, "%d/%m/%Y")
    starting_date = pytz.timezone(TIME_ZONE).localize(starting_date)

    dt_first_challenge_offer = datetime.strptime(first_challenge_offer, "%H:%M")
    dt_first_challenge_offer = pytz.timezone(TIME_ZONE).localize(dt_first_challenge_offer)

    offer_window = timedelta(hours=offer_window)
    challenge_duration = timedelta(hours=challenge_duration)
    challenge_window = timedelta(hours=challenge_window)

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
        base_chest_amount=base_chest_amount,
    )

    if u is not None:
        print(f"User {u.username} successfully created.")
        print("-" * 20)
    else:
        raise ValueError("Something went wrong! User not created.")

    s = Status.objects.create(user=u, state=init_state)
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
                objective=objective,
                amount=amount,
                android_tag=random_uuid,
                server_tag=random_uuid,
                accepted=challenge_accepted,
            )

            current_time = dt_latest

        current_date += timedelta(days=1)

    print(f"Challenges successfully created for user {u.username}.")
    print(f"Last challenge ends at: {dt_end}.")
    print("-" * 20)
    print("Test user creation completed successfully.")

