from django.contrib import admin

from user.models import User, Activity, Reward


class UserAdmin(admin.ModelAdmin):
    list_display = (
        "username", "is_superuser", "date_joined", "experiment", "starting_date")


admin.site.register(User, UserAdmin)


class ActivityAdmin(admin.ModelAdmin):
    list_display = (
        "id", "get_user", "dt", "dt_last_boot", "step_last_boot", "step_midnight")

    @admin.display(ordering='username', description='username')
    def get_user(self, obj):
        return obj.user.username


admin.site.register(Activity, ActivityAdmin)


class RewardAdmin(admin.ModelAdmin):
    list_display = (
        "id", "get_user", "date", "objective", "amount", "condition", "accessible",
        "objective_reached", "objective_reached_dt", "cashed_out", "cashed_out_dt")

    @admin.display(ordering='username', description='username')
    def get_user(self, obj):
        return obj.user.username


admin.site.register(Reward, RewardAdmin)



