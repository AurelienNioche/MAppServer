from django.contrib.auth import authenticate
from django.db import IntegrityError

from user.models import User


def login(email, password):
    # Return User object if a backend authenticated the credentials,
    # None otherwise
    return authenticate(email=email, password=password)


def sign_up(email, password, condition,
            experiment_name,
            gender=None, age=None,
            *args, **kwargs):

    """
        Creates a new learner and returns its id
    """

    try:
        u = User.objects.create_user(
            email=email,
            password=password,
            gender=gender,
            age=age,
            condition=condition,
            experiment_name=experiment_name)
        from experimental_condition import experimental_condition
        experimental_condition.user_creation(user=u, *args, **kwargs)

    except IntegrityError as e:
        raise e

    return u

