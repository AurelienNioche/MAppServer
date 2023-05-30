from django.db import models
from utils.time import string_to_datetime

from user.models import User


class UserProgress(models.Model):

    # Set at the moment of the creation ----------------------------------
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=None, null=False)
    step_number = models.IntegerField(default=None, null=False)

    def new_entry(self, user, timestamp, step_number):
        self.user = user
        self.step_number = step_number
        self.timestamp = string_to_datetime(timestamp)
        self.save()
