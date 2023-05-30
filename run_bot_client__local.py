import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

import json
import websocket


class Bot(websocket.WebSocketApp):

    def __init__(self, url="ws://127.0.0.1:8000/ws",
                 username="123test",
                 waiting_time=1):

        super().__init__(
            url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open)

        self.username = username

        # Parameters
        self.waiting_time = waiting_time

        # Set afterwards
        self.user_id = None

    @staticmethod
    def on_message(ws, json_string):

        print(f"I received: {json_string}")
        message = json.loads(json_string)
        subject = message["subject"]
        rsp = {"login": ws.after_login,
               }[subject]()
        return ws.send_message(rsp)

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
            "subject": "login",
            "username": self.username
        }
        self.send_message(message)

    def after_login(self, ws, message):

        if message["ok"]:
            ws.user_id = message["user_id"]
            return
        else:
            comment = message["comment"] if "comment" in message else None
            raise Exception(f"Can't login! Additional message is: {comment}")

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
    ws = Bot()
    ws.run_forever()


if __name__ == "__main__":

    main()
