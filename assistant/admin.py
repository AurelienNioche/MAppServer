from django.contrib import admin
from .models import *


class BaseAdmin(admin.ModelAdmin):
    @admin.display(ordering="user__username", description="user__username")
    def get_user(self, obj):
        return obj.user.username


@admin.register(ActionPlan)
class ActionPlanAdmin(BaseAdmin):
    list_display = ("get_user", "date", "value")


# @admin.register(Schedule)
# class ScheduleAdmin(BaseAdmin):
#     list_display = ("get_user", "breakfast", "lunch", "dinner")
#
#
# @admin.register(Alpha)
# class AlphaAdmin(BaseAdmin):
#     list_display = ("get_user", "date", "alpha")
#
#
# @admin.register(Velocity)
# class VelocityAdmin(BaseAdmin):
#     list_display = ("get_user", "dt", "timestep_index", "velocity")
#
#
# @admin.register(Position)
# class PositionAdmin(BaseAdmin):
#     list_display = ("get_user", "dt", "timestep_index", "position")
#
#
# @admin.register(Action)
# class ActionAdmin(BaseAdmin):
#     list_display = ("get_user", "date", "timestep_index", "action")
