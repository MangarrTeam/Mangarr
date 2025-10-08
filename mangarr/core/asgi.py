import os
import django
from django.core.asgi import get_asgi_application
from core.thread_manager import stop_all_threads
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import websockets.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

django_asgi_app = get_asgi_application()

async def lifespan(scope, receive, send):
    if scope["type"] != "lifespan":
        return
    while True:
        message = await receive()
        if message["type"] == "lifespan.startup":
            print("[ASGI] Starting background threads...")
            from core.background import start_background_tasks
            start_background_tasks()
            await send({"type": "lifespan.startup.complete"})
        elif message["type"] == "lifespan.shutdown":
            print("[ASGI] Gracefully stopping threads...")
            stop_all_threads()
            await send({"type": "lifespan.shutdown.complete"})
            break


application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websockets.routing.websocket_urlpatterns
        )
    ),
    "lifespan": lifespan
})
