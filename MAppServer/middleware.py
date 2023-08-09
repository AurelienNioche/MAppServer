import pytz
import zoneinfo
from django.utils import timezone
# from MAppServer.settings import TIME_ZONE


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # tzname = request.session.get("django_timezone")
        timezone.activate(zoneinfo.ZoneInfo("Europe/London"))
        return self.get_response(request)
