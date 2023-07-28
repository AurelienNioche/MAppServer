from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils import timezone

import datetime


# Utils -----------------------------------------------------------------------

def snake_to_camel(snake_str):
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def convert_datetime_to_android_timestamp(dt):
    if dt is None:
        return -1
    return int(dt.timestamp() * 1000)


def convert_date_to_android_timestamp(date):
    if date is None:
        return -1
    # Take midday as timestamp
    ts_python = datetime.datetime.fromordinal(date.toordinal()) + datetime.timedelta(days=0.5)
    return convert_datetime_to_android_timestamp(ts_python)

# ------------------------------------------------------------------------------


class MAppModel(models.Model):

    def to_android_dict(self):
        android_dict = {}
        for k, v in self.__dict__.items():
            if not k.startswith("_"):
                if "dt" in k:
                    k = k.replace("dt", "ts")
                    v = convert_datetime_to_android_timestamp(v)
                android_dict[snake_to_camel(k)] = v

        return android_dict

    def to_csv_row(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}


class User(AbstractUser, MAppModel):

    date_joined = models.DateTimeField(auto_now_add=True)

    # All below should be optional only for the superuser
    experiment = models.TextField(blank=True, null=False)
    starting_date = models.DateField(default=None, null=False)  # Should be optional only for the superuser
    base_chest_amount = models.FloatField(default=None, null=False)  # Should be optional only for the superuser

    objects = UserManager()

    # removes email from REQUIRED_FIELDS
    REQUIRED_FIELDS = ['experiment', 'starting_date', 'base_chest_amount', 'daily_objective']


class Activity(MAppModel):

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


class Challenge(MAppModel):

    # Set at creation
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dt = models.DateTimeField(default=None, null=False)
    objective = models.IntegerField(default=None, null=False)
    amount = models.FloatField(default=None, null=False)

    # Set after interaction with the user
    accepted = models.BooleanField(default=False, null=False)
    accepted_dt = models.DateTimeField(default=None, null=True)
    objective_reached = models.BooleanField(default=False, null=False)
    objective_reached_dt = models.DateTimeField(default=None, null=True)
    cashed_out = models.BooleanField(default=False, null=False)
    cashed_out_dt = models.DateTimeField(default=None, null=True)


class Status(MAppModel):

    class Meta:
        verbose_name_plural = "statuses"

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    last_update_dt = models.DateTimeField(default=None, null=True)
    chest_amount = models.FloatField(default=None, null=True)
    state = models.CharField(default=None, null=True, max_length=256)
    day_of_the_week = models.CharField(default=None, null=True, max_length=256)
    day_of_the_month = models.CharField(default=None, null=True, max_length=256)
    month = models.CharField(default=None, null=True, max_length=256)
    step_day = models.IntegerField(default=None, null=True)
    error = models.CharField(default=None, null=True, max_length=256)


class ConnectionToServer(MAppModel):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dt = models.DateTimeField(default=timezone.now, null=False)


class Interaction(MAppModel):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dt = models.DateTimeField(default=None, null=False)
    event = models.CharField(default=None, null=True, max_length=256)
    android_id = models.IntegerField(default=None, null=False)

