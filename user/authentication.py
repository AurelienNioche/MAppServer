from django.contrib.auth import authenticate
from django.db import IntegrityError

from user.models import User


def login(username):

    """
        Return User object if a backend authenticated the credentials,
        None otherwise
    """

    return authenticate(username=username)


def sign_up(username, *args, **kwargs):

    """
        Creates a new user
    """

    try:
        u = User.objects.create_user(username, *args, **kwargs)

    except IntegrityError as e:
        raise e

    return u

