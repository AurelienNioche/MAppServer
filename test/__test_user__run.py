import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MAppServer.settings")
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

import json
import websocket

from MAppServer.settings import APP_VERSION
from user.models import User, Status


URL = "ws://127.0.0.1:8080/ws"
USERNAME = "123test"

# NGROK_URL = "ff87-130-209-252-154.ngrok-free.app"
# URL = f"wss://{NGROK_URL}/ws",


class Bot(websocket.WebSocketApp):
    """
    ws://192.168.0.14:8080/ws
    wss://samoa.dcs.gla.ac.uk/mapp/ws
    """

    def __init__(
        self,
        waiting_time=2,
    ):
        super().__init__(
            URL,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )

        self.username = USERNAME

        # Websocket parameters
        self.waiting_time = waiting_time

    @staticmethod
    def on_message(ws, json_string):
        print(f"I received: {json_string}")
        msg = json.loads(json_string)
        subject = msg["subject"]
        f = getattr(ws, f"after_{subject}")
        f(msg)

    @staticmethod
    def on_error(ws, error):
        print(f"I got error: {error}")

    @staticmethod
    def on_close(ws, close_status_code, close_msg):
        print(f"I'm closing.")
        if close_status_code or close_msg:
            print(f"Close status code: {close_status_code}")
            print(f"Close message: {close_msg}")

    @staticmethod
    def on_open(ws):
        print("I'm open.")
        ws.login()

    def send_message(self, message):
        string_msg = json.dumps(message, indent=4)
        print(f"I'm sending: {string_msg}")
        self.send(string_msg)

    def login(self):
        message = {
            "subject": "login",
            "appVersion": APP_VERSION,
            "username": self.username,
            "resetUser": False,
        }
        self.send_message(message)

    def after_login(self, msg):
        print("After login: giving a fake update")
        assert msg["ok"]
        # Give a fake activity update
        self.update()

    def update(self):
        message = {
            "subject": "update",
            "appVersion": APP_VERSION,
            "username": self.username,
            "steps": json.dumps([]),
            "status": json.dumps(
                User.objects.filter(username=self.username)
                .first()
                .status_set.first()
                .to_android_dict()
            ),
            "interactions": json.dumps([]),
            "unSyncedChallenges": json.dumps([]),
        }
        self.send_message(message)

    def after_update(self, msg):
        print("Update done, test successful!")
        self.close()


def main():
    websocket.enableTrace(True)
    ws = Bot()
    ws.run_forever()


if __name__ == "__main__":
    # from test_user__create import test_user__create
    # test_user__create()
    main()
