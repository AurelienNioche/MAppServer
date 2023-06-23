import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from django.db import transaction
import pytz
import numpy as np
import datetime
import uuid
import json

from user.models import User, Reward, Status
from MAppServer.settings import TIME_ZONE

@transaction.atomic
def test_user__seb():

    seed = 123
    username = "sebastian"
    starting_date = datetime.datetime.now(pytz.timezone(TIME_ZONE))
    experiment_name = "not-even-an-alpha-test"
    base_chest_amount = 0
    daily_objective = 300

    # starting_date = utils.time.string_to_date(f"{starting_date}")
    # ending_date = starting_date + datetime.timedelta(days=n_days)

    np.random.seed(seed)

    u = User.objects.filter(username=username).first()
    if u is not None:
        print(f"Deleting old test user {u.username}")
        u.delete()

    u = User.objects.create_user(
        username=username,
        experiment=experiment_name,
        starting_date=starting_date,
        base_chest_amount=base_chest_amount,
        daily_objective=daily_objective,
    )

    if u is not None:
        print(f"User {u.username} successfully created")
    else:
        raise ValueError("Something went wrong! User not created")
    # ---------------------------------------------------------------
    # Create rewards
    objectives = [50, ] * 6
    print(objectives)
    cum_objectives = np.cumsum(objectives)
    print(cum_objectives)
    starting_at = [cum_objectives[i - 1] if i > 0 else 0 for i in range(len(objectives))]
    print(starting_at)
    for i in range(len(objectives)):
        r = Reward(
            user=u,
            date=starting_date,
            amount=0.1,
            objective=int(cum_objectives[i]),
            starting_at=int(starting_at[i])
        )
        r.save()
        print(json.dumps(r.to_dict(), indent=4))

    print(f"Rewards successfully created for user {u.username}")
    # ---------------------------------------------------------------
    # Create status
    status = Status(user=u, )
    status.save()
    print(f"Status successfully created for user {u.username}")
    print("*" * 100)


if __name__ == "__main__":
    test_user__seb()

