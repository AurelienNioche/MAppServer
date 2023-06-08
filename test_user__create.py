import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from django.db import transaction
import numpy as np
import datetime

from user.models import User, Reward
import utils.time


class Condition:
    CONSTANT = "constant"
    PROPORTIONAL_QUANTITY = "proportional_quantity"
    INCREMENTAL_REWARD_AMOUNT = "incremental_reward_amount"
    INCREMENTAL_OBJECTIVE = "incremental_objective"

    @classmethod
    def list(cls):
        return [k for k in cls.__dict__.keys() if k[0].isupper()]
@transaction.atomic
def test_user__create():

    username = "123test"
    starting_date = "2023-06-12"
    n_days = 21
    experiment_name = "Michele's students"

    starting_date = utils.time.string_to_date(f"{starting_date}")
    ending_date = starting_date + datetime.timedelta(days=n_days)

    np.random.seed(123)

    u = User.objects.filter(username=username).first()
    if u is not None:
        print("Deleting old test user")
        u.delete()

    user = User.objects.create_user(
        username=username,
        experiment=experiment_name,
        starting_date=starting_date,
        ending_date=ending_date
    )

    if user is not None:
        print("Test user successfully created")
    else:
        raise ValueError("Something went wrong! User not created")

    """"
    Constant: get money if reached the goal
    Proportional quantised: we have scales, based how much you walked you fall under scale. Ex.:
    1.4k steps → 30p,
    1.4k steps → 30p,
    1.4k steps → 30p,
    1.4k steps → 30p,
    1.4k steps → 30p,
    £1.5 per day, 7k steps
    
    Incremental v1
    1.4k steps → 10p,
    1.4k steps → 20p,
    1.4k steps → 30p,
    1.4k steps → 40p,
    1.4k steps → 50p,
    £1.5 per day, 7k steps
    
    Incremental v2  --- MAYBE WE WANT TO REVERT THAT?
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

    # Shuffle conditions
    np.random.shuffle(user_cond)

    while len(user_cond) < n_days:
        user_cond.insert(0, Condition.CONSTANT)   # That's the + 1 day

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
            objectives = np.cumsum([1400, ] * n_rep)
            amounts = [0.30, ] * n_rep

        elif cond == Condition.INCREMENTAL_OBJECTIVE:
            n_rep = 5
            objectives = np.cumsum([700, 1050, 1400, 1750, 2100])
            amounts = [0.30, ] * n_rep

        elif cond == Condition.INCREMENTAL_REWARD_AMOUNT:
            n_rep = 5
            objectives = np.cumsum([1400, ] * n_rep)
            amounts = [10, 20, 30, 40, 50]

        else:
            raise ValueError

        for i in range(n_rep):
            Reward(
                user=user,
                date=current_date,
                amount=amounts[i],
                objective=objectives[i],
                condition=cond
            ).save()

        current_date += datetime.timedelta(days=1)


if __name__ == "__main__":
    test_user__create()
