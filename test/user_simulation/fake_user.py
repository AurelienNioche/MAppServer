import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
from django.db import transaction

application = get_wsgi_application()

from MAppServer.settings import TIME_ZONE
from user.models import User, Activity, Challenge, Status

import json
import websocket
from datetime import datetime, timedelta
import uuid
import pytz


class FakeUser:

    sec_delta_between_steps = 60**2
    step_delta_between_steps = 20
    n = 10
    base_step = 10
    base_sec = 0

    def __init__(self, username):
        self.username = username
        self.now = datetime.now()

    def _generate_fake_steps(self) -> list[dict]:
        step_events = []
        for i in range(self.n):
            step_events.append(
                {
                    "ts": (self.now.timestamp() - self.base_sec - i*self.sec_delta_between_steps)*1000,
                    "step_midnight": self.base_step + self.step_delta_between_steps*i,
                    "android_id": i
                }
            )
        return step_events

    def _generate_unsynced_challenges(self) -> list[dict]:
        return []

    def _generate_status(self):

        return User.objects.filter(username=self.username).first().status_set.first().to_android_dict()

    def update(self):

        return {
            "now": self.now.strftime("%d/%m/%Y %H:%M:%S"),
            "steps": json.dumps(self._generate_fake_steps()),
            "unsynced_challenges": json.dumps(self._generate_unsynced_challenges()),
            "status": json.dumps(self._generate_status())
        }
