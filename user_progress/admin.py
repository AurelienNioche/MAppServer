from django.contrib import admin

from . models import UserProgress


class UserProgressAdmin(admin.ModelAdmin):
    list_display = (
        "id", "user_id", "timestamp")


admin.site.register(UserProgress, UserProgressAdmin)
