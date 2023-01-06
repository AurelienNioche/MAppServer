from django.contrib import admin

from . models import Condition


class ConditionAdmin(admin.ModelAdmin):
    list_display = [f.name for f in Condition._meta.fields]


admin.site.register(Condition, ConditionAdmin)
