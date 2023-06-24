import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

import pandas as pd
from django.utils import timezone

from user.models import User


os.makedirs("data", exist_ok=True)


def main():
    date = timezone.now().date()
    ts = f"{date.year}-{date.month}-{date.day}"

    users = User.objects.filter(is_superuser=False)
    for u in users:
        print(f"Saving data for user {u.id}")
        row_list = []
        for r in u.reward_set.all():
            row_list.append(r.to_csv_row())

        df = pd.DataFrame(row_list)
        df.to_csv(f"data/{u.username}_rewards_{ts}.csv")

        row_list = []
        for a in u.activity_set.all():
            row_list.append(a.to_csv_row())

        df = pd.DataFrame(row_list)
        df.to_csv(f"data/{u.username}_activities_{ts}.csv")

        # row_list = []
        # for a in u.activity_set.all():
        #     row_list.append(a.to_csv_row())
        #
        # df = pd.DataFrame(row_list)
        # df.to_csv(f"data/{u.username}_activities.csv")


if __name__ == "__main__":

    main()
    print("Done!")
