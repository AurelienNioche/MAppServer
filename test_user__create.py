import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from user.models import User


def test_user__create():

    u = User.objects.filter(username="123test").first()
    if u is not None:
        print("Deleting old test user")
        u.delete()

    user = User.objects.create_user(username="123test", experiment="test", condition="rewarded_only_at_goal")

    if user is not None:
        print("Test user successfully created")
    else:
        raise ValueError("Something went wrong! User not created")


if __name__ == "__main__":
    test_user__create()
