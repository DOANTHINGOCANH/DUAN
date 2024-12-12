import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from Duan_Mingle.mxh.routing import websocket_urlpatterns # Đảm bảo đúng tên module

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DuAn_Mingle.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns  # Chỉ cần gọi trực tiếp
        )
    ),
})

