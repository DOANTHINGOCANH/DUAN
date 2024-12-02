# DuAn_Mingle/mxh/routing.py
from django.urls import re_path
from .consumers import ChatConsumer

websocket_urlpatterns = [
    # Định tuyến cho chat nhóm
    re_path(r'ws/messages/group/(?P<group_id>\d+)/$', ChatConsumer.as_asgi(), name='group_chat_ws'),

    # Định tuyến cho chat cá nhân
    re_path(r'ws/messages/user/(?P<user_id>\d+)/$', ChatConsumer.as_asgi(), name='user_chat_ws'),
]
