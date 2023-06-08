from django.contrib.auth.models import AbstractUser
from django.db import models

import datetime


class User(AbstractUser):

    date_joined = models.DateTimeField(auto_now_add=True)

    experiment = models.TextField(blank=True, null=True)  # Optional
    starting_date = models.DateField(null=False)
    ending_date = models.DateField(null=False)

    REQUIRED_FIELDS = [starting_date, ending_date]  # removes email from REQUIRED_FIELDS


class Activity(models.Model):

    class Meta:
        verbose_name_plural = "activities"
        # constraints = [
        #     models.UniqueConstraint(
        #         fields=['user', 'timestamp'],
        #         name='only one activity at a time for a single user')
        # ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dt = models.DateTimeField(default=None, null=False)
    dt_last_boot = models.DateTimeField(default=None, null=False)
    step_last_boot = models.IntegerField(default=None, null=False)
    step_midnight = models.IntegerField(default=None, null=False)


class Reward(models.Model):

    # Set at creation
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=None, null=False)
    objective = models.IntegerField(default=None, null=False)
    amount = models.FloatField(default=None, null=False)
    condition = models.CharField(default=None, null=True, max_length=256)

    # Set after interaction with the user
    accessible = models.BooleanField(default=True, null=False)
    objective_reached = models.BooleanField(default=False, null=False)
    objective_reached_dt = models.DateTimeField(default=None, null=True)
    cashed_out = models.BooleanField(default=False, null=False)
    cashed_out_dt = models.DateTimeField(default=None, null=True)

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": datetime.datetime.fromordinal(self.date.toordinal()).timestamp(),
            "objective": self.objective,
            "amount": self.amount,
            "objectiveReached": self.objective_reached,
            "cashedOut": self.cashed_out,
            "accessible": self.accessible
        }
