import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
        except json.JSONDecodeError:
            return  # ignora mensagens malformadas

        msg_type = text_data_json.get("type")

        # Trata mensagens do tipo ping
        if msg_type == "ping":
            await self.send(text_data=json.dumps({"type": "pong"}))
            return

        # Trata mensagens normais de chat
        message = text_data_json.get("message")
        username = text_data_json.get("username")

        if message and username:
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "chat_message", "message": message, "username": username},
            )

    async def chat_message(self, event):
        message = event["message"]
        username = event["username"]

        await self.send(
            text_data=json.dumps({"message": message, "username": username})
        )
