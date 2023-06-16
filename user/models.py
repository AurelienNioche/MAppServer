from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models

import datetime
import uuid


class User(AbstractUser):

    date_joined = models.DateTimeField(auto_now_add=True)

    experiment = models.TextField(blank=True, null=True)  # Should be optional only for the superuser
    starting_date = models.DateField(default=None, null=True)  # Should be optional only for the superuser
    base_chest_amount = models.FloatField(default=None, null=True)  # Should be optional only for the superuser
    daily_objective = models.IntegerField(default=None, null=True)  # Should be optional only for the superuser

    REQUIRED_FIELDS = []  # removes email from REQUIRED_FIELDS


class Activity(models.Model):

    class Meta:
        verbose_name_plural = "activities"
        # constraints = [
        #     models.UniqueConstraint(
        #         fields=['user', 'android_id'],
        #         name='only one activity with the same android_id for a single user')
        # ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    android_id = models.IntegerField(default=None, null=False)
    dt = models.DateTimeField(default=None, null=False)
    dt_last_boot = models.DateTimeField(default=None, null=False)
    step_last_boot = models.IntegerField(default=None, null=False)
    step_midnight = models.IntegerField(default=None, null=False)


class Reward(models.Model):

    # Set at creation
    user = models.ForeignKey(User, on_delete=models.CASCADE)                  # ex: ffe21
    date = models.DateField(default=None, null=False)                         # ex: 2023/03/28
    objective = models.IntegerField(default=None, null=False)                 # ex: 1400  (cumulative over the current day)
    amount = models.FloatField(default=None, null=False)                      # ex: 0.10  (not cumulative)
    condition = models.CharField(default=None, null=True, max_length=256)     # ex: "proportional_quantity"

    # Set after interaction with the user
    accessible = models.BooleanField(default=False, null=False)        # Default need to be false
    objective_reached = models.BooleanField(default=False, null=False)
    objective_reached_dt = models.DateTimeField(default=None, null=True)
    cashed_out = models.BooleanField(default=False, null=False)
    cashed_out_dt = models.DateTimeField(default=None, null=True)

    serverTag = models.CharField(default=None, null=True, max_length=256)
    localTag = models.CharField(default=None, null=True, max_length=256)

    def to_dict(self):
        # Take midday as timestamp
        ts = datetime.datetime.fromordinal(self.date.toordinal()) + datetime.timedelta(days=0.5)
        ts = int(ts.timestamp() * 1000)
        initial_tag = str(uuid.uuid4())
        return {
            "id": self.id,
            "ts": ts,
            "objective": self.objective,
            "amount": self.amount,
            "objectiveReached": self.objective_reached,
            "cashedOut": self.cashed_out,
            "accessible": self.accessible,
            "serverTag": initial_tag,
            "localTag": initial_tag
        }


class Status(models.Model):

    class Meta:
        verbose_name_plural = "statuses"

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    last_update_dt = models.DateTimeField(default=None, null=True)
    chest_amount = models.FloatField(default=None, null=True)
    daily_objective = models.IntegerField(default=None, null=True)
    daily_objective_reached = models.BooleanField(default=False, null=True)
    state = models.CharField(default=None, null=True, max_length=256)
    objective = models.IntegerField(default=None, null=True)
    objective_reached = models.BinaryField(default=None, null=True)
    amount = models.FloatField(default=None, null=True)
    day_of_the_month = models.CharField(default=None, null=True, max_length=256)
    day_of_the_week = models.CharField(default=None, null=True, max_length=256)
    month = models.CharField(default=None, null=True, max_length=256)
    step_number_day = models.IntegerField(default=None, null=True)
    step_number_reward = models.IntegerField(default=None, null=True)
    reward_id = models.IntegerField(default=None, null=True)
