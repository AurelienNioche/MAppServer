from django.contrib.auth.models import AbstractUser
from django.db import models

import utils.time


class User(AbstractUser):

    experiment = models.TextField(blank=True, null=False)
    condition = models.TextField(blank=True, null=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    REQUIRED_FIELDS = [experiment, condition]  # removes email from REQUIRED_FIELDS


class Activity(models.Model):

    class Meta:
        verbose_name_plural = "activities"
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'timestamp'],
                name='only one activity at the time for a single user')
        ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=None, null=False)
    step_number = models.IntegerField(default=None, null=False)
    rewardable = models.BooleanField(default=True)


class Reward(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=None, null=False)
    amount = models.FloatField(default=None, null=False)
    comment = models.CharField(default="", null=True, max_length=256)
