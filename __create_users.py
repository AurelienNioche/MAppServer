import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from MAppServer.settings import TIME_ZONE

from django.db import transaction
import pytz
import datetime
import pandas as pd

from MAppServer.settings import USER_CREATION_CSV_PATH

from user.models import User, Reward, Status


@transaction.atomic
def main():

    experiment_name = "experiment_June_2023"
    base_chest_amount = 6.00
    daily_objective = 7000

    csv = pd.read_csv(f"{USER_CREATION_CSV_PATH}")

    csv["user"] = csv["user"].astype(str)

    for row in csv.itertuples():
        print(row)
        username = row.user
        # assert len(username) == 4 or username.startswith("michele"), f"Username {username} is not 4 characters long."
        dt = datetime.datetime.strptime(row.date, '%d/%m/%Y')
        date = pytz.timezone(TIME_ZONE).localize(dt).date()
        u = User.objects.filter(username=username).first()
        if u is None:
            print(f"Creating user {username}")
            u = User(
                username=username,
                experiment=experiment_name,
                starting_date=date,  # We assume that in the CSV, the rewards are ordered by date
                base_chest_amount=base_chest_amount,
                daily_objective=daily_objective,
            )
            u.save()
            print("-" * 20)

            status = Status(user=u, )
            status.save()
            print(f"Status successfully created for user {u.username}")
            print("-" * 20)

        objective = row.objective
        r = Reward.objects.filter(user=u, date=date, objective=objective).first()
        if r is None:
            r = Reward(
                user=u,
                date=date,
                amount=row.amount,
                objective=objective,
                starting_at=row.starting_at,
                condition=row.condition)
            r.save()
            print(f"Reward {r.id} successfully created for user {u.username}.")
        else:
            print(f"Reward {r.id} NOT CREATED for {u.username}: a similar reward already existed.")


if __name__ == "__main__":
    out = input(f"Are you sure you want to create the users using the file `{USER_CREATION_CSV_PATH}`? (Y/N)")
    if out.lower() in ('y', 'yes'):
        main()
