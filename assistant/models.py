from django.db import models
from user.models import User
from django.contrib.postgres.fields import ArrayField


class UserModel(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # 5D array: n_timestep, n_action, n_position, n_velocity, n_velocity
    alpha = ArrayField(ArrayField(ArrayField(ArrayField(ArrayField(models.FloatField())))))

    breakfast = models.TimeField()
    lunch = models.TimeField()
    dinner = models.TimeField()

