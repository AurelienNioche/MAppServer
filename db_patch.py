import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from user.models import User


def main():

    for u in User.objects.exclude(is_superuser=True):
        if 'test' not in u.email:
            ###
            # Do modification
            ###
            u.save()


if __name__ == "__main__":
    main()
    print("Done!")
