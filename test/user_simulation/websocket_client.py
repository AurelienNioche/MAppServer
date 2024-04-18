import traceback
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MAppServer.settings")
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

import json
import websocket
from datetime import datetime, timedelta

from MAppServer.settings import APP_VERSION
from user.models import User


class DefaultUser:

    def __init__(self, username="123test"):
        self.username = username

    def now(self):
        return datetime.now()

    def steps(self):
        return [
            {
                "ts": (self.now() - timedelta(minutes=30)).timestamp()*1000,
                "step_midnight": 1,
                "android_id": 0
            },
            {
                "ts": (self.now() - timedelta(minutes=20)).timestamp()*1000,
                "step_midnight": 2,
                "android_id": 1
            },
            {
                "ts": (self.now() - timedelta(minutes=10)).timestamp()*1000,
                "step_midnight": 3,
                "android_id": 2
            }
        ]

    def update(self):
        return {
            "now": self.now().strftime("%d/%m/%Y %H:%M:%S"),
            "steps": json.dumps(self.steps()),
        }

    def done(self):

        return True


class Bot(websocket.WebSocketApp):
    """
    ws://192.168.0.14:8080/ws
    wss://samoa.dcs.gla.ac.uk/mapp/ws
    """

    def __init__(
        self,
        url,
        user,
        username,
    ):
        super().__init__(
            url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )

        if user is None:
            user = DefaultUser(username=username)

        self.user = user

    @staticmethod
    def on_message(ws, json_string):
        # print(f"I received: {json_string}")
        msg = json.loads(json_string)
        subject = msg["subject"]
        f = getattr(ws, f"after_{subject}")
        f(msg)

    @staticmethod
    def on_error(ws, error):
        print("I encountered an error.")
        print(traceback.print_exc())
        raise Exception(f"I encountered an error: {error}")

    @staticmethod
    def on_close(ws, close_status_code, close_msg):
        # print(f"I'm closing.")
        if close_status_code or close_msg:
            print(f"Close status code: {close_status_code}")
            print(f"Close message: {close_msg}")

    @staticmethod
    def on_open(ws):
        # print("I'm open.")
        ws.login()

    def send_message(self, message):
        string_msg = json.dumps(message, indent=4)
        # print(f"I'm sending: {string_msg}")
        self.send(string_msg)

    def login(self):
        message = {
            "subject": "login",
            "appVersion": APP_VERSION,
            "username": self.user.username,
            "resetUser": False,
        }
        self.send_message(message)

    def after_login(self, msg):
        # print("After login: switch to update")
        assert msg["ok"]
        # Give a fake activity update
        self.update()

    def update(self):
        default_status = User.objects.filter(username=self.user.username).first().status_set.first().to_android_dict()
        default_now = datetime.now()
        message = {
            "subject": "update",
            "appVersion": APP_VERSION,
            "username": self.user.username,
            "now": default_now.strftime("%d/%m/%Y %H:%M:%S"),
            "status": json.dumps(default_status),
            "steps": json.dumps([]),
            "interactions": json.dumps([]),
            "unSyncedChallenges": json.dumps([]),
        }
        message.update(self.user.update())
        self.send_message(message)

    def after_update(self, msg):
        # print("Update done!")
        if self.user.done():
            # print("Test successful!")
            self.close()
        else:
            self.update()


def run_bot(url="ws://127.0.0.1:8080/ws", user=None, username=None):
    websocket.enableTrace(False)
    bot = Bot(url=url, user=user, username=username)
    bot.run_forever()
