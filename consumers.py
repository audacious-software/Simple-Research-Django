# chat/consumers.py
import json

from channels.generic.websocket import WebsocketConsumer

class EventConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, code):
        pass

    def receive(self, text_data=None, bytes_data=None): # pylint: disable=unused-argument
        print('text_data: %s' % text_data)
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        self.send(text_data=json.dumps({"message": message}))
