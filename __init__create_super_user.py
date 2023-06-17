import datetime
import os

import pytz

os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from MAppServer.settings \
    import EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, TIME_ZONE
from user.models import User


def create_super_user():

    User.objects.create_superuser(username=f'{EMAIL_HOST_USER}',
                                  email=f'{EMAIL_HOST_USER}',
                                  password=f'{EMAIL_HOST_PASSWORD}',
                                  experiment="superuser",
                                  starting_date=datetime.datetime.now(tz=pytz.timezone(TIME_ZONE)),
                                  base_chest_amount=-1,
                                  daily_objective=-1,)
    print("Superuser created successfully.")


if __name__ == "__main__":
    create_super_user()
