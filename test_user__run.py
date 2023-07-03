import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

import json
import websocket


class Bot(websocket.WebSocketApp):
    """
    ws://192.168.0.101:8000/ws
    wss://samoa.dcs.gla.ac.uk/mapp/ws
    """
    def __init__(
            self, url="ws://192.168.0.14:8080/ws",
            username="123test",
            waiting_time=2):

        super().__init__(
            url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open)

        self.username = username

        # Websocket parameters
        self.waiting_time = waiting_time

    @staticmethod
    def on_message(ws, json_string):

        print(f"I received: {json_string}")
        msg = json.loads(json_string)
        subject = msg["subject"]
        f = getattr(ws, f'after_{subject}')
        f(msg)

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
            "username": self.username,
            "resetUser": False
        }
        self.send_message(message)

    def after_login(self, msg):
        print("after login, I'm done")
        # assert msg["ok"]
        # if "comment" in msg:
        #     print("comment", msg["comment"])
        #
        # # Give a fake activity update
        # self.update()

    # def update(self):
    #     now = datetime.datetime.now(tz=pytz.timezone('europe/london'))
    #     activity_list = []
    #
    #     step_number = 0
    #     n_epoch = 5
    #
    #     for t in reversed(range(n_epoch)):
    #         ts = now - datetime.timedelta(minutes=5*t)
    #         activity_list.append(dict(
    #             timestamp=utils.time.datetime_to_sting(ts),
    #             step_number=7500-500*t,
    #         ))
    #     rsp = dict(
    #         subject="update",
    #         username=self.username,
    #         latest_reward_timestamp=None,
    #         activity=activity_list,
    #     )
    #     self.send_message(rsp)
    #
    # def after_update(self, msg):
    #     print(msg)
    #     print("DONE!")


def main():

    websocket.enableTrace(True)
    ws = Bot()
    ws.run_forever()


if __name__ == "__main__":
    # from test_user__create import test_user__create
    # test_user__create()
    main()
