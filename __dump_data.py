import os

try:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                          "MAppServer.settings")
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
except:
    os.chdir(os.path.expanduser("~/DjangoApps/MAppServer"))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                          "MAppServer.settings")
    from django.core.wsgi import get_wsgi_application

    application = get_wsgi_application()

import pandas as pd
from datetime import datetime

from MAppServer.settings import SERVER_DATA_DIR, SERVER_LATEST_DUMP_PATH

from user.models import User
from tqdm import tqdm


def main():

    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d_%H-%M-%S")

    folder = f"{SERVER_DATA_DIR}/dump_{now_str}"
    os.makedirs(folder, exist_ok=True)

    users = User.objects.filter(is_superuser=False)

    df = pd.DataFrame([u.to_csv_row() for u in users])
    df.to_csv(f"{folder}/users_{now_str}.csv")

    for u in tqdm(users):
        for entry_type in ("reward", "activity", "interaction", "log"):
            row_list = []
            for r in getattr(u, f"{entry_type}_set").all():
                row_list.append(r.to_csv_row(date_format="%Y-%m-%d %H:%M:%S.%f%z"))

            df = pd.DataFrame(row_list)
            df.to_csv(f"{folder}/{u.username}_{entry_type}_{now_str}.csv")

    print(f"Done! Data exported in folder `{folder}`.")

    if os.path.exists(SERVER_LATEST_DUMP_PATH):
        os.unlink(SERVER_LATEST_DUMP_PATH)
    os.symlink(folder, SERVER_LATEST_DUMP_PATH)
    print(f"Symlink created (`{SERVER_LATEST_DUMP_PATH}`).")


if __name__ == "__main__":

    main()
