import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

import pandas as pd
from datetime import datetime

from MAppServer.settings import SERVER_DATA_DIR

from user.models import User
from tqdm import tqdm


now = datetime.now()
now_str = now.strftime("%Y-%m-%d_%H-%M-%S")

folder = f"{SERVER_DATA_DIR}/dump_{now_str}"
os.makedirs(folder, exist_ok=True)


def main():

    users = User.objects.filter(is_superuser=False)
    for u in tqdm(users):
        # print(f"Saving data for user {u.id}")
        row_list = []
        for r in u.reward_set.all():
            row_list.append(r.to_csv_row())

        df = pd.DataFrame(row_list)
        df.to_csv(f"{folder}/{u.username}_rewards_{now_str}.csv")

        row_list = []
        for a in u.activity_set.all():
            row_list.append(a.to_csv_row())

        df = pd.DataFrame(row_list)
        df.to_csv(f"{folder}/{u.username}_activities_{now_str}.csv")

        row_list = []
        for entry in u.interaction_set.all():
            row_list.append(entry.to_csv_row())

        df = pd.DataFrame(row_list)
        df.to_csv(f"{folder}/{u.username}_interactions_{now_str}.csv")

        row_list = []
        for entry in u.log_set.all():
            row_list.append(entry.to_csv_row())

        df = pd.DataFrame(row_list)
        df.to_csv(f"{folder}/{u.username}_logs_{now_str}.csv")

    print(f"Done! Data exported in folder `{folder}`.")


if __name__ == "__main__":

    main()
