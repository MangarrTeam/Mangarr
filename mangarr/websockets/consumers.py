from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
import json
import copy

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def notify_clients(new_data):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "processes_updates",
        {
            "type": "send_update",  # matches the consumer method name
            "data": new_data,
        }
    )


def deep_merge(dict_a, dict_b):
    result = copy.deepcopy(dict_a)
    for key, value in dict_b.items():
        if (
            key in result and
            isinstance(result[key], dict) and
            isinstance(value, dict)
        ):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


class ProcessesConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "processes_updates"
        self.datas = {
            "scanning": {
                "manga": 0,
                "chapters": 0
            },
            "downloading": {
                "current": 0,
                "of": 0
            }
        }

        await self.channel_layer.group_add(self.group_name, self.channel_name)        
        await self.accept()

        data = await self.get_data_from_db()
        await self.send(text_data=json.dumps({"message": "Connected!", "data": data}))

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        pass

    async def send_update(self, event):
        self.datas = deep_merge(self.datas, event["data"])

        await self.send(text_data=json.dumps(self.datas))


    @sync_to_async
    def get_data_from_db(self):
        return self.datas