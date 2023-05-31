import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from user.models import User
from reception_desk.reception_desk import RequestHandler
import utils.time
from datetime import datetime
import pytz

from MAppServer.settings import TIME_ZONE


u = User.objects.filter(username="123test").first()
RequestHandler.log_progress(dict(
    subject="log_progress",
    user_id=u.id,
    progress=[
        {
            "timestamp": utils.time.datetime_to_sting(datetime.now(tz=pytz.timezone(TIME_ZONE))),
            "step_number": 34
        },
    ]))
