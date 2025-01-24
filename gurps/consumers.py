import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Pega o identificador do chat da URL
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]  # ex: chat_4
        self.room_group_name = f"chat_{self.room_name}"

        # Adiciona o usuário ao grupo baseado no nome do chat
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # Aceita a conexão WebSocket
        await self.accept()

    async def disconnect(self, close_code):
        # Remove o usuário do grupo quando desconectar
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Recebe a mensagem do WebSocket
    async def receive(self, text_data):
        # Recebe a mensagem
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        username = text_data_json["username"]

        # Envia a mensagem para o grupo (todos os usuários conectados a este chat)
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "chat_message", "message": message, "username": username},
        )

    # Envia a mensagem para o WebSocket
    async def chat_message(self, event):
        # Recebe a mensagem do grupo e envia para o WebSocket do usuário
        message = event["message"]
        username = event["username"]
        await self.send(
            text_data=json.dumps({"message": message, "username": username})
        )
