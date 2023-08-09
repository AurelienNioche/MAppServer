from django.contrib import admin

from user.models import User, Activity, Status, ConnectionToServer, Interaction, Challenge


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        "username", "is_superuser", "date_joined", "experiment", "starting_date",]


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = [
        "id", "get_user", "dt", "dt_last_boot", "step_last_boot", "step_midnight", "android_id"]

    @admin.display(ordering='user__username', description='user__username')
    def get_user(self, obj):
        return obj.user.username


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = [
        "id", "get_user",
        "objective", "amount",
        "dt_offer", "dt_offer_end",
        "dt", "dt_end",
        "accepted", "accepted_dt",
        "objective_reached", "objective_reached_dt",
        "cashed_out", "cashed_out_dt"]

    @admin.display(ordering='user__username', description='user__username')
    def get_user(self, obj):
        return obj.user.username


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):

    list_display = [
        "id", "get_user", "last_update_dt", "state", "error",
        "chest_amount",
        "step_day", "current_challenge",
        "day_of_the_week", "day_of_the_month", "month"]

    @admin.display(ordering='user__username', description='user__username')
    def get_user(self, obj):
        return obj.user.username


@admin.register(ConnectionToServer)
class Admin(admin.ModelAdmin):

    list_display = ["id", "get_user", "dt"]

    @admin.display(ordering='user__username', description='user__username')
    def get_user(self, obj):
        return obj.user.username


@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):

    list_display = ["id", "get_user", "dt", "event", "android_id"]

    @admin.display(ordering='user__username', description='user__username')
    def get_user(self, obj):
        return obj.user.username
