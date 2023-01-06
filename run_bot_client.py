import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

import websocket

from bot_client.random_socket import RandomSocket


def run_random():

    websocket.enableTrace(True)
    ws = RandomSocket()
    ws.run_forever()


def main():

    run_random()


if __name__ == "__main__":

    run_random()
