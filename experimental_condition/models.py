from django.db import models

from user.models import User


class ConditionManager(models.Manager):

    def create(self, user):

        obj = super().create(user=user)
        return obj


class Condition(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    objects = ConditionManager()

