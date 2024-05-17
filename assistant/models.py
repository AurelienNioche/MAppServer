from django.db import models
from user.models import User
from django.contrib.postgres.fields import ArrayField


class ActionPlan(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    value = ArrayField(models.IntegerField())
