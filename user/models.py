from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils import timezone

import datetime


class User(AbstractUser):

    date_joined = models.DateTimeField(auto_now_add=True)

    experiment = models.TextField(blank=True, null=False)  # Should be optional only for the superuser
    starting_date = models.DateField(default=None, null=False)  # Should be optional only for the superuser
    base_chest_amount = models.FloatField(default=None, null=False)  # Should be optional only for the superuser
    daily_objective = models.IntegerField(default=None, null=False)  # Should be optional only for the superuser

    objects = UserManager()

    REQUIRED_FIELDS = ['experiment', 'starting_date', 'base_chest_amount', 'daily_objective']  # removes email from REQUIRED_FIELDS


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

    def to_csv_row(self):
        return {
            "user": self.user.username,
            "id": self.id,
            "dt": self.dt,
            "dt_last_boot": self.dt_last_boot,
            "step_last_boot": self.step_last_boot,
            "step_midnight": self.step_midnight,
        }

    def to_android_dict(self):
        ts = int(self.dt.timestamp() * 1000)
        ts_last_boot = int(self.dt_last_boot.timestamp() * 1000)
        return {
            "id": self.android_id,  # Not id because server id and android id are different
            "ts": ts,
            "tsLastBoot": ts_last_boot,
            "stepLastBoot": self.step_last_boot,
            "stepMidnight": self.step_midnight
        }


class Reward(models.Model):

    # Set at creation
    user = models.ForeignKey(User, on_delete=models.CASCADE)                  # ex: ffe21
    date = models.DateField(default=None, null=False)                         # ex: 2023/03/28
    objective = models.IntegerField(default=None, null=False)                 # ex: 1400  (cumulative over the current day)
    starting_at = models.IntegerField(default=None, null=False)
    amount = models.FloatField(default=None, null=False)                      # ex: 0.10  (not cumulative)
    condition = models.CharField(default=None, null=True, max_length=256)     # ex: "proportional_quantity"

    # Set after interaction with the user
    objective_reached = models.BooleanField(default=False, null=False)
    objective_reached_dt = models.DateTimeField(default=None, null=True)
    cashed_out = models.BooleanField(default=False, null=False)
    cashed_out_dt = models.DateTimeField(default=None, null=True)
    revealed_by_button = models.BooleanField(default=False, null=False)
    revealed_by_notification = models.BooleanField(default=False, null=False)
    revealed_dt = models.DateTimeField(default=None, null=True)

    def to_android_dict(self):
        # Take midday as timestamp
        ts_python = datetime.datetime.fromordinal(self.date.toordinal()) + datetime.timedelta(days=0.5)
        ts = int(ts_python.timestamp() * 1000)
        cashed_out_ts = int(self.cashed_out_dt.timestamp()*1000) if self.cashed_out_dt is not None else -1
        revealed_ts = int(self.revealed_dt.timestamp()*1000) if self.revealed_dt is not None else -1
        objective_reached_ts = int(self.objective_reached_dt.timestamp()*1000) if self.objective_reached_dt is not None else -1
        return {
            "id": self.id,
            "ts": ts,
            "objective": self.objective,
            "startingAt": self.starting_at,
            "amount": self.amount,
            "objectiveReached": self.objective_reached,
            "objectiveReachedTs": objective_reached_ts,
            "cashedOut": self.cashed_out,
            "cashedOutTs": cashed_out_ts,
            "revealedTs": revealed_ts,
            "revealedByButton": self.revealed_by_button,
            "revealedByNotification": self.revealed_by_notification,
        }

    def to_csv_row(self):

        return {
            "user": self.user.username,
            "id": self.id,
            "date": self.date,
            "starting_at": self.starting_at,
            "objective": self.objective,
            "amount": self.amount,
            "objective_reached": self.objective_reached,
            "objective_reached_dt": self.objective_reached_dt,
            "cashed_out": self.cashed_out,
            "cashed_out_dt": self.cashed_out_dt,
            "condition": self.condition,
        }


class Status(models.Model):

    class Meta:
        verbose_name_plural = "statuses"

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    last_update_dt = models.DateTimeField(default=None, null=True)
    chest_amount = models.FloatField(default=None, null=True)
    daily_objective = models.IntegerField(default=None, null=True)
    state = models.CharField(default=None, null=True, max_length=256)
    objective = models.IntegerField(default=None, null=True)
    starting_at = models.IntegerField(default=None, null=True)
    amount = models.FloatField(default=None, null=True)
    day_of_the_month = models.CharField(default=None, null=True, max_length=256)
    day_of_the_week = models.CharField(default=None, null=True, max_length=256)
    month = models.CharField(default=None, null=True, max_length=256)
    step_number = models.IntegerField(default=None, null=True)
    reward_id = models.IntegerField(default=None, null=True)
    error = models.CharField(default=None, null=True, max_length=256)

    def to_dict(self): return {
        "id": self.id,
        "user": self.user.username,
        "last_update_dt": self.last_update_dt,
        "chest_amount": self.chest_amount,
        "daily_objective": self.daily_objective,
        "state": self.state,
        "objective": self.objective,
        "starting_at": self.starting_at,
        "amount": self.amount,
        "day_of_the_month": self.day_of_the_month,
        "day_of_the_week": self.day_of_the_week,
        "month": self.month,
        "step_number": self.step_number,
        "reward_id": self.reward_id,
        "error": self.error,
    }

    def to_android_dict(self): return {
            "id": self.id,
            "state": self.state,
            "dailyObjective": self.daily_objective,
            "chestAmount": self.chest_amount,
            "dayOfTheWeek": self.day_of_the_week,
            "dayOfTheMonth": self.day_of_the_month,
            "month": self.month,
            "stepNumber": self.step_number,
            "rewardId": self.reward_id,
            "objective": self.objective,
            "startingAt": self.starting_at,
            "amount": self.amount,
            "error": self.error,
        }


class Log(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dt = models.DateTimeField(default=timezone.now, null=False)

    def to_csv_row(self):
        return {
            "user": self.user.username,
            "id": self.id,
            "dt": self.dt,
        }


class Interaction(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dt = models.DateTimeField(default=None, null=False)
    event = models.CharField(default=None, null=True, max_length=256)
    android_id = models.IntegerField(default=None, null=False)

    def to_csv_row(self):
        return {
            "user": self.user.username,
            "id": self.id,
            "dt": self.dt,
            "event": self.event,
        }
