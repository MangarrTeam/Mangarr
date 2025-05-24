from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path("stats/", consumers.ProcessesConsumer.as_asgi()),
]