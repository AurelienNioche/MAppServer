from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    experiment = models.TextField(blank=True, null=True)
    condition = models.TextField(blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    REQUIRED_FIELDS = []  # removes email from REQUIRED_FIELDS
