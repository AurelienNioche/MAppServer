from django.db import models
from utils.time import string_to_datetime

from user.models import User


class Interaction(models.Model):

    # Set at the moment of the creation ----------------------------------
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=None, null=True)

    def register_user_interaction(self, timestamp):

        self.timestamp = string_to_datetime(timestamp)
        self.save()
