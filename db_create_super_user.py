import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from MAppServer.settings \
    import EMAIL_HOST_USER, EMAIL_HOST_PASSWORD
from user.models import User


def create_super_user():

    User.objects.create_superuser(f'{EMAIL_HOST_USER}',
                                  f'{EMAIL_HOST_PASSWORD}')


if __name__ == "__main__":
    create_super_user()
    print("Done!")
