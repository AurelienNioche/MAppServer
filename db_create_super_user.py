import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from MAppServer.settings \
    import EMAIL_HOST_USER, EMAIL_HOST_PASSWORD
from user.models import User


def create_super_user():

    User.objects.create_superuser(username=f'{EMAIL_HOST_USER}',
                                  email=f'{EMAIL_HOST_USER}',
                                  password=f'{EMAIL_HOST_PASSWORD}')
    print("Superuser created successfully.")


if __name__ == "__main__":
    create_super_user()
