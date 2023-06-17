import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from user.models import User


if __name__ == "__main__":
    rsp = input("Are you sure you want to DELETE ALL THE USERS? (Y/N)")
    if rsp.lower() in ('y', 'yes'):
        User.objects.all().delete()
        print("All users deleted.")
    else:
        print("No users deleted.")

