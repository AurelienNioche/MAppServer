from django.contrib import admin
from .models import *


class BaseAdmin(admin.ModelAdmin):
    @admin.display(ordering="user__username", description="user__username")
    def get_user(self, obj):
        return obj.user.username


@admin.register(ActionPlan)
class ActionPlanAdmin(BaseAdmin):
    list_display = ("get_user", "date", "value")

