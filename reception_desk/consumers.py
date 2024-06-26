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
            print("I received content that appears not to be JSON:")
            print(text)
            return
        # print("Received:", json.dumps(text_data_json, indent=4))
        # message = text_data_json['message']
        response = treat_request(text_data_json)
        resp = json.dumps(response, indent=4)
        # print("Send:", resp)
        if bytes_data is not None:
            self.send(bytes_data=resp.encode())
        else:
            self.send(text_data=resp)
