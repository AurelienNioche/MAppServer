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

INIT_STATE = "experimentNotStarted"


@transaction.atomic
def create_test_user():

    challenge_offer_hours = [8, 12, 20]
    challenge_offer_times = [time(hour=h, minute=0, second=0, microsecond=0, tzinfo=pytz.timezone(TIME_ZONE))
                             for h in challenge_offer_hours]

    username = "123test"
    starting_date = datetime.now(tz=pytz.timezone(TIME_ZONE))
    experiment_name = "not-even-an-alpha-test"
    base_chest_amount = 6
    objective = 1000
    amount = 0.4
    n_day = 2
    offer_window = timedelta(hours=1)
    challenge_window = timedelta(hours=2)
    init_delta_after_offer_end = timedelta(hours=1)

    print("BASIC TEST USER CREATION")

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
        for ch_t in challenge_offer_times:

            dt_offer_begin = datetime(
                current_date.year, current_date.month, current_date.day,
                ch_t.hour, ch_t.minute, ch_t.second, ch_t.microsecond,
                current_date.tzinfo)

            # uuid_tag = uuid.uuid4()
            # uuid_tag_str = str(uuid_tag)

            dt_offer_end = dt_offer_begin + offer_window
            dt = dt_offer_end + init_delta_after_offer_end
            dt_end = dt + challenge_window

            Challenge.objects.create(
                user=u,
                dt_offer_begin=dt_offer_begin,
                dt_offer_end=dt_offer_end,
                dt_begin=dt,
                dt_end=dt_end,
                objective=objective,
                amount=amount)
                # serverTag=uuid_tag_str,
                # localTag=uuid_tag_str)

        current_date += timedelta(days=1)

    print(f"Challenges successfully created for user {u.username}.")
    print("-" * 20)
    print("Test user creation completed successfully.")


if __name__ == "__main__":
    create_test_user()
