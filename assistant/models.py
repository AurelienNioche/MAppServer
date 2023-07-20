from django.db import models
from user.models import User
from django.contrib.postgres.fields import ArrayField


class Schedule(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    breakfast = models.TimeField()
    lunch = models.TimeField()
    dinner = models.TimeField()


class Alpha(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()

    # 5D array: n_timestep, n_action, n_position, n_velocity, n_velocity
    alpha = ArrayField(ArrayField(ArrayField(ArrayField(ArrayField(models.FloatField())))))


class Velocity(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dt = models.DateTimeField()
    timestep_index = models.IntegerField()
    velocity = models.FloatField()


class Position(models.Model):
    """
    Position of the user is, in this context, the number of daily steps done so far since midnight that day.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dt = models.DateTimeField()
    timestep_index = models.IntegerField()
    position = models.FloatField()


class Action(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    timestep_index = models.IntegerField()
    action = models.IntegerField()
