import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

import pandas as pd

from user.models import User


os.makedirs("data", exist_ok=True)


def main():

    users = User.objects.filter(is_superuser=False)
    for u in users:
        row_list = []
        for r in u.reward_set.all():
            print(f"user {u.id}")
            print(r.id)
            row = {
            }
            # for resp_idx, meaning in enumerate(q.possible_replies.all()):
            #     row.update({f"pos_reply_{resp_idx}": meaning.meaning})

            row_list.append(row)

        df = pd.DataFrame(row_list)
        df.to_csv(f"data/{u.username}_rewards.csv")


if __name__ == "__main__":

    main()
    print("Done!")
