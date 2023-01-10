import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from user.authentication import sign_up
from user.models import User


def main():

    print("WELCOME! This will help you to create a user!")

    experiment_name = input("experiment name:")
    condition = input("condition:")

    email = input("email:")
    if User.objects.filter(email=email).first():
        print("Warning! User already exists!")
        erase_user = input("erase existing user (enter 'yes' or 'y' to continue)?")
        if erase_user:
            User.objects.filter(email=email).first().delete()
            print("previous user erased")
            print(f"email:{email}")
        else:
            print("can not create user with same email. Operation canceled")
            exit(0)

    password = input("password:")

    while True:
        gender = input("gender (enter 'female', 'male' or 'other'):")
        if gender not in (User.MALE, User.FEMALE, User.OTHER):
            print("I did not get the answer! Try again!")
        else:
            break

    gender = int(gender)

    while True:
        try:
            age = int(input("age:"))
            break
        except Exception:
            print("I did not get the answer! Try again!")

    ready = input("create user (enter 'yes' or 'y' to continue)?")
    if ready not in ('y', 'yes'):
        print("Operation cancelled")
        exit(0)

    user = sign_up(
        email=email,
        password=password,
        gender=gender,
        age=age,
        experiment_name=experiment_name,
        condition=condition)

    if user is not None:
        print("Success!")
    else:
        raise ValueError("Something went wrong!")


if __name__ == "__main__":
    main()
