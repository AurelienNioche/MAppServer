from django.contrib import admin

from user.models import User, Activity, Reward


class UserAdmin(admin.ModelAdmin):
    list_display = (
        "username", "is_superuser", "date_joined", "last_login", "experiment", "condition")


admin.site.register(User, UserAdmin)


class ActivityAdmin(admin.ModelAdmin):
    list_display = (
        "id", "get_user", "timestamp", "step_number")

    @admin.display(ordering='username', description='username')
    def get_user(self, obj):
        return obj.user.username


admin.site.register(Activity, ActivityAdmin)


class RewardAdmin(admin.ModelAdmin):
    list_display = (
        "id", "get_user", "timestamp", "amount")

    @admin.display(ordering='username', description='username')
    def get_user(self, obj):
        return obj.user.username


admin.site.register(Reward, RewardAdmin)



