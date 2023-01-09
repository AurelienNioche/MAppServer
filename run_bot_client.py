import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

import json
import websocket

from reception_desk.reception_desk import Subject


class RandomSocket(websocket.WebSocketApp):

    def __init__(self, url="ws://localhost:8000",
                 email="test@test.com",
                 password='1234',
                 gender='male',
                 age='25',
                 waiting_time=1):

        super().__init__(
            url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open)

        self.email = email
        self.password = password
        self.gender = gender
        self.age = age
        self.waiting_time = waiting_time

        self.user_id = None

    @staticmethod
    def on_message(ws, json_string):

        print(f"I received: {json_string}")
        message = json.loads(json_string)

        if message["subject"] == Subject.LOGIN:
            if message["ok"]:
                ws.user_id = message["user_id"]
                return
            else:
                raise Exception("Can't login!")

        else:
            raise ValueError

    @staticmethod
    def on_error(ws, error):
        print(f"I got error: {error}")

    @staticmethod
    def on_close(ws, close_status_code, close_msg):
        print(f"I'm closing. Code={close_status_code}. Msg={close_msg}")

    @staticmethod
    def on_open(ws):

        print("I'm open")
        ws.login()

    def send_message(self, message):

        string_msg = json.dumps(message)
        print(f"I'm sending {string_msg}")
        self.send(string_msg)

    def login(self):

        message = {
            "subject": Subject.LOGIN,
            "email": self.email,
            "password": self.password}
        self.send_message(message)

    # def signup(self):
    #
    #     message = Request(
    #         subject=Request.SIGN_UP,
    #         email=self.email,
    #         password=self.password,
    #         gender=self.gender,
    #         mother_tongue=self.mother_tongue,
    #         other_language=self.other_language
    #     )
    #     self.send_message(message)


def main():

    websocket.enableTrace(True)
    ws = RandomSocket()
    ws.run_forever()
    print("yo")


if __name__ == "__main__":

    main()
