from django.contrib import admin

from user.models import User, Activity, Reward, Status


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "username", "is_superuser", "date_joined", "experiment", "starting_date")


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = (
        "id", "get_user", "dt", "dt_last_boot", "step_last_boot", "step_midnight")

    @admin.display(ordering='username', description='username')
    def get_user(self, obj):
        return obj.user.username


@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = (
        "id", "get_user", "date", "objective", "amount", "condition", "accessible",
        "objective_reached", "objective_reached_dt", "cashed_out", "cashed_out_dt")

    @admin.display(ordering='username', description='username')
    def get_user(self, obj):
        return obj.user.username


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):

    list_display = (
        "id", "get_user", "last_update_dt",
        "amount", "chest_amount",
        "daily_objective", "step_number_day",
        "state", "reward_id", "objective", "step_number_reward",
        "day_of_the_week", "day_of_the_month", "month")

    @admin.display(ordering='username', description='username')
    def get_user(self, obj):
        return obj.user.username




