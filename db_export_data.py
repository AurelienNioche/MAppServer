import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

import pandas as pd

from user.models import User


os.makedirs("data", exist_ok=True)


def main():
    # TODO: NEEDS TO BE UPDATED WITH NEW DATA STRUCTURE
    row_list = []

    users = User.objects.filter(is_superuser=False)
    i = -1
    for u in users:

        if 'test' in u.email:
            print(f"ignore: {u.email}")
            continue
        else:
            i += 1
            print(f"user {i}: {u.email}")

            row = {
                "user": u.email,
                "experiment": u.experiment,
                "condition": u.condition,
            }
            # for resp_idx, meaning in enumerate(q.possible_replies.all()):
            #     row.update({f"pos_reply_{resp_idx}": meaning.meaning})
            row_list.append(row)

    df = pd.DataFrame(row_list)
    df.to_csv("data/data_full.csv")


if __name__ == "__main__":

    main()
    print("Done!")
