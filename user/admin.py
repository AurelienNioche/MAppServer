from django.contrib import admin
from user.models import (
    User,
    Activity,
    Status,
    ConnectionToServer,
    Interaction,
    Challenge,
)


class BaseAdmin(admin.ModelAdmin):
    @admin.display(ordering="user__username", description="user__username")
    def get_user(self, obj):
        return obj.user.username


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        "username",
        "is_superuser",
        "date_joined",
        "experiment",
        "starting_date",
    ]


@admin.register(Activity)
class ActivityAdmin(BaseAdmin):
    list_display = [
        "id",
        "get_user",
        "dt",
        "dt_last_boot",
        "step_last_boot",
        "step_midnight",
        "android_id",
    ]


@admin.register(Challenge)
class ChallengeAdmin(BaseAdmin):
    list_display = [
        "id",
        "get_user",
        "objective",
        "amount",
        "dt_offer_begin",
        "dt_offer_end",
        "dt_begin",
        "dt_end",
        "accepted",
        "accepted_dt",
        "objective_reached",
        "objective_reached_dt",
        "cashed_out",
        "cashed_out_dt",
    ]


@admin.register(Status)
class StatusAdmin(BaseAdmin):
    list_display = [
        "id",
        "get_user",
        "last_update_dt",
        "state",
        "error",
        "chest_amount",
        "step_day",
        "current_challenge",
        "day_of_the_week",
        "day_of_the_month",
        "month",
    ]


@admin.register(ConnectionToServer)
class ConnectionToServerAdmin(BaseAdmin):
    list_display = ["id", "get_user", "dt"]


@admin.register(Interaction)
class InteractionAdmin(BaseAdmin):
    list_display = ["id", "get_user", "dt", "event", "android_id"]
