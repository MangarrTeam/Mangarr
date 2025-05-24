from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
import json
import copy
from django.core.cache import cache

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

def default_datas() -> dict:
    return {
            "scanning": {
                "manga": 0,
                "chapters": 0
            },
            "downloading": {
                "current": 0,
                "of": 0
            }
        }

class ProcessesConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope["user"].id
        self.group_name = "processes_updates"

        await self.channel_layer.group_add(self.group_name, self.channel_name)        
        await self.accept()

        await self.send(text_data=json.dumps({"message": "Connected!", "data": default_datas()}))

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        pass

    async def send_update(self, event):
        data = deep_merge(await sync_to_async(cache.get)(f'process_data_{self.user_id}') or default_datas(), event["data"])
        await sync_to_async(cache.set)(f'process_data_{self.user_id}', data)

        await self.send(text_data=json.dumps(data))