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


class Condition:
    CONSTANT = "constant"
    PROPORTIONAL_QUANTITY = "proportional_quantity"
    INCREMENTAL_REWARD_AMOUNT = "incremental_reward_amount"
    INCREMENTAL_OBJECTIVE = "incremental_objective"

    @classmethod
    def list(cls):
        return [k for k in cls.__dict__.keys() if k[0].isupper()]


def create_user(
    username,
    experiment_name,
    starting_date,
    base_chest_amount,
    daily_objective,
):

    u = User.objects.filter(username=username).first()
    if u is not None:
        print("Deleting previous user with the same name")
        u.delete()

    u = User.objects.create_user(
        username=username,
        experiment=experiment_name,
        starting_date=starting_date,
        base_chest_amount=base_chest_amount,
        daily_objective=daily_objective,
    )

    if u is not None:
        print("User successfully created")
    else:
        raise ValueError("Something went wrong! User not created")

    return u


def create_status(u):

    status = Status(user=u, )
    status.save()
    print("Status successfully created")


def create_rewards(user, starting_date, n_days, seed):
    """
    Constant: get money if reached the goal
    Proportional quantised: we have scales, based how much you walked you fall under scale. Ex.:
    1.4k steps → 30p,
    1.4k steps → 30p,
    1.4k steps → 30p,
    1.4k steps → 30p,
    1.4k steps → 30p,
    £1.5 per day, 7k steps

    Incremental v1   // --- MAYBE WE WANT TO REVERSE THE ORDER?
    1.4k steps → 10p,
    1.4k steps → 20p,
    1.4k steps → 30p,
    1.4k steps → 40p,
    1.4k steps → 50p,
    £1.5 per day, 7k steps

    Incremental v2  // --- OR MAYBE WE WANT TO REVERSE THE ORDER HERE?
    0.70k steps → 30p,
    1.05k steps → 30p,
    1.4k steps → 30p,
    1.75k steps → 30p,
    2.1k steps → 30p,
    £1.5 per day, 7k steps
    """

    user_cond = []
    uniq_cond = Condition.list()
    n_rep_cond = n_days // len(uniq_cond)
    for cond in uniq_cond:
        for _ in range(n_rep_cond):
            user_cond.append(getattr(Condition, cond))

    np.random.seed(seed)
    # Shuffle conditions
    np.random.shuffle(user_cond)

    while len(user_cond) < n_days:
        user_cond.insert(0, Condition.CONSTANT)  # That's the + 1 day

    print("User conditions", user_cond)

    # ---------------------------------------------------------------

    current_date = starting_date
    for cond in user_cond:
        if cond == Condition.CONSTANT:
            n_rep = 1
            objectives = [7000, ]
            amounts = [1.5, ]

        elif cond == Condition.PROPORTIONAL_QUANTITY:
            n_rep = 5
            objectives = [1400, ] * n_rep
            amounts = [0.30, ] * n_rep

        elif cond == Condition.INCREMENTAL_OBJECTIVE:
            n_rep = 5
            objectives = [700, 1050, 1400, 1750, 2100]
            amounts = [0.30, ] * n_rep

        elif cond == Condition.INCREMENTAL_REWARD_AMOUNT:
            n_rep = 5
            objectives = [1400, ] * n_rep
            amounts = [0.10, 0.20, 0.30, 0.40, 0.50]

        else:
            raise ValueError

        cum_objectives = np.cumsum(objectives)
        starting_at = [cum_objectives[i-1] if i > 0 else 0 for i in range(n_rep)]

        for i in range(n_rep):
            uuid_tag = uuid.uuid4()
            uuid_tag_str = str(uuid_tag)

            Reward(
                user=user,
                date=current_date,
                amount=amounts[i],
                objective=cum_objectives[i],
                starting_at=starting_at[i],
                condition=cond,
                serverTag=uuid_tag_str,
                localTag=uuid_tag_str
            ).save()

        current_date += datetime.timedelta(days=1)

    print("Reward successfully created. User conditions:", user_cond)


@transaction.atomic
def test_user__basic():

    seed = 123
    username = "123test"
    starting_date = datetime.datetime.now(pytz.timezone(TIME_ZONE))
    experiment_name = "Michele's students"
    base_chest_amount = 6
    daily_objective = 7000

    # starting_date = utils.time.string_to_date(f"{starting_date}")
    # ending_date = starting_date + datetime.timedelta(days=n_days)

    np.random.seed(seed)

    u = User.objects.filter(username=username).first()
    if u is not None:
        print("Deleting old test user")
        u.delete()

    u = User.objects.create_user(
        username=username,
        experiment=experiment_name,
        starting_date=starting_date,
        base_chest_amount=base_chest_amount,
        daily_objective=daily_objective,
    )

    if u is not None:
        print("Test user successfully created")
    else:
        raise ValueError("Something went wrong! User not created")
    # ---------------------------------------------------------------
    # Create rewards
    objectives = [10, ] * 2
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

    print("Rewards successfully created")
    # ---------------------------------------------------------------
    # Create status
    status = Status(user=u, )
    status.save()
    print("Status successfully created")


def test_user_xp_like__create(
        seed=123,
        username="123test",
        experiment_name="alpha-test"):

    starting_date = datetime.datetime.now(pytz.timezone(TIME_ZONE))
    base_chest_amount = 6
    daily_objective = 7000
    n_days = 30

    u = create_user(username=username,
                    experiment_name=experiment_name,
                    starting_date=starting_date,
                    base_chest_amount=base_chest_amount,
                    daily_objective=daily_objective)
    create_status(u=u)
    create_rewards(user=u,
                   starting_date=starting_date,
                   n_days=n_days,
                   seed=seed)

    assert Reward.objects.filter(user=u).count() > 0 and Status.objects.filter(user=u).count() > 0, "Something went wrong!"


def create_test_user():
    test_user__basic()
    # test_user_xp_like__create()


if __name__ == "__main__":
    create_test_user()

