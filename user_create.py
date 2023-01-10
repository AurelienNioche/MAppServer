import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from user.authentication import sign_up
from user.models import User


def main():

    user = sign_up(
        email="test@test.com",
        password="1234",
        gender="male",
        age="age",
        experiment_name="test",
        condition="test")

    if user is not None:
        print("Success!")
    else:
        raise ValueError("Something went wrong! User not created")


if __name__ == "__main__":
    main()
