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
import glob

from MAppServer.settings import USER_CREATION_CSV_PATH
from user.models import User, Reward, Status


def identify_which_files_to_use():

    for file in glob.glob(f"{USER_CREATION_CSV_PATH}/*.csv"):
        print(f"Considering the file `{file}`...")

        df = pd.read_csv(file)
        df["user"] = df["user"].astype(str)

        should_create_users = True
        for user in df.user.unique():
            u = User.objects.filter(username=user).first()
            if u is None:
                print(f"User {user} does not exist.")

            else:
                print(f"User {user} exists. I'll skip this file.")
                should_create_users = False
                break

        if should_create_users:
            out = input(f"Are you sure you want to create the users using the file `{file}`? (Y/N)")
            if out.lower() in ('y', 'yes'):
                print(f"Creating users from the file {file}...")
                print("-" * 20)
                create_users_from_df(df)
            else:
                print(f"Skipping the file {file}.")

        print("-" * 20)


def create_users_from_df(df):

    experiment_name = "experiment_June_2023"
    base_chest_amount = 6.00
    daily_objective = 7000

    for row in df.itertuples():
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
                starting_date=date,  # We assume that in the CSV, the challenges are ordered by date
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


@transaction.atomic
def main():
    identify_which_files_to_use()


if __name__ == "__main__":
    main()
