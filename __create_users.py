import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from MAppServer.settings import TIME_ZONE

from django.db import transaction
import pytz
import datetime
import uuid
import pandas as pd

from user.models import User, Reward, Status
from utils.time import string_to_date


@transaction.atomic
def main():

    experiment_name = "experiment_June_2023"
    base_chest_amount = 6.00
    daily_objective = 7000
    csv = pd.read_csv("data/user_creation/rewards.csv")

    for row in csv.itertuples():
        print(row)
        username = row.user
        u = User.objects.filter(username=username).first()
        if u is None:
            print(f"Creating user {username}")

            dt = datetime.datetime.strptime(row.date, '%Y-%m-%d')
            starting_date = pytz.timezone(TIME_ZONE).localize(dt).date()

            u = User(
                username=username,
                experiment=experiment_name,
                starting_date=starting_date,
                base_chest_amount=base_chest_amount,
                daily_objective=daily_objective,
            )
            u.save()
            print("-" * 20)

            status = Status(user=u, )
            status.save()
            print(f"Status successfully created for user {u.username}")
            print("-" * 20)

        uuid_tag = uuid.uuid4()
        uuid_tag_str = str(uuid_tag)

        date = string_to_date(row.date)
        objective = row.objective
        r = Reward.objects.filter(user=u, date=date, objective=objective).first()
        if r is None:
            r = Reward(
                user=u,
                date=date,
                amount=row.amount,
                objective=objective,
                starting_at=row.starting_at,
                condition=row.condition,
                serverTag=uuid_tag_str,
                localTag=uuid_tag_str)
            r.save()
            print(f"Reward {r.id} successfully created for user {u.username}.")
        else:
            print(f"Reward {r.id} NOT CREATED for {u.username}: a similar reward already existed.")


if __name__ == "__main__":
    main()
