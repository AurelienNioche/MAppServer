from django.contrib import admin

from user.models import User


class UserAdmin(admin.ModelAdmin):
    list_display = (
        "username", "is_superuser", "date_joined", "last_login", "experiment", "condition")


admin.site.register(User, UserAdmin)
