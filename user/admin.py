from django.contrib import admin

from user.models import User


class UserAdmin(admin.ModelAdmin):
    list_display = (
        "id", "email", "is_superuser", "date_joined", "condition",
        "last_login", "gender", "age")


admin.site.register(User, UserAdmin)
