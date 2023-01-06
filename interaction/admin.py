from django.contrib import admin

from . models import Interaction


class InteractionAdmin(admin.ModelAdmin):
    list_display = (
        "id", "user_id", "timestamp")


admin.site.register(Interaction, InteractionAdmin)
