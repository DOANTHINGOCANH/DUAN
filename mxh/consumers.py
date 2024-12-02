# DuAn_Mingle/mxh/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Message, Group, User

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Lấy group_id hoặc user_id từ URL
        self.group_id = self.scope['url_route']['kwargs'].get('group_id')
        self.user_id = self.scope['url_route']['kwargs'].get('user_id')

        # Nếu có group_id thì kết nối tới nhóm, nếu không kết nối cá nhân
        if self.group_id:
            self.group_name = f'group_{self.group_id}'
            # Kiểm tra quyền truy cập vào nhóm (optional)
        else:
            self.group_name = f'user_{self.user_id}'

        # Join the group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        # Accept the WebSocket connection
        await self.accept()

    async def disconnect(self, close_code):
        # Leave the group on disconnect
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # Nhận tin nhắn từ WebSocket và gửi vào group
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Lưu tin nhắn vào database
        if self.group_id:
            group = Group.objects.get(id=self.group_id)
            Message.objects.create(text=message, group=group)
        else:
            user = User.objects.get(id=self.user_id)
            Message.objects.create(text=message, recipient=user, sender=self.scope['user'])

        # Gửi tin nhắn tới nhóm
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    # Nhận và gửi tin nhắn tới WebSocket
    async def chat_message(self, event):
        message = event['message']

        # Gửi tin nhắn tới WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))
