from channels.generic.websocket import WebsocketConsumer
import json

from . reception_desk import treat_request


class WebSocketConsumer(WebsocketConsumer):

    def connect(self):
        self.accept()

    def disconnect(self, close_code):

        print(f'Disconnection! Close code: {close_code}')

    def receive(self, text_data=None, bytes_data=None):

        if bytes_data is not None:
            text = bytes_data.decode("utf-8")
        elif text_data is not None:
            text = text_data
        else:
            raise ValueError

        try:
            text_data_json = json.loads(text)
        except:
            print("Received:", text)
            print("Does not appear to be JSON")
            return

        print("Received:", text_data_json)
        # message = text_data_json['message']

        response = treat_request(text_data_json)

        print("Send:", response)
        resp = json.dumps(response)
        if bytes_data is not None:
            self.send(bytes_data=resp.encode())
        else:
            self.send(text_data=resp)
