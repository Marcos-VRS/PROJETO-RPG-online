"""WebSocket consumers do gurps.

Um consumer único (`ChatConsumer`) cuida de chat E eventos de jogo em tempo real
na mesma conexão e mesmo grupo de canal (`chat_<campanha_id>`).

Tipos de mensagem aceitos:
- ``ping`` → server responde ``pong``.
- ``message`` + ``username`` (sem type) → chat normal.
- ``scene_state_set`` (só GM) → cliente envia o estado de cena inteiro. Server
  valida estrutura + permissão, persiste em ``Campanha.scene_state`` e faz
  broadcast pra todos do grupo via ``scene_state_changed``.

Estrutura do scene_state (v2):
    {
        "version": 2,
        "scenes": [
            {"id": str, "name": str, "character_ids": [int, ...]},
            ...
        ],
        "active_scene_id": str | null
    }

Limite: até 10 cenas por campanha (validação server-side).
"""
import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from gurps.models import Campanha

MAX_SCENES_PER_CAMPAIGN = 10


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
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        msg_type = data.get("type")

        if msg_type == "ping":
            await self.send(text_data=json.dumps({"type": "pong"}))
            return

        if msg_type == "scene_state_set":
            await self._handle_scene_state_set(data)
            return

        # Chat (sem `type`) — compat com chat.js existente.
        message = data.get("message")
        username = data.get("username")
        if message and username:
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "chat_message", "message": message, "username": username},
            )

    async def chat_message(self, event):
        await self.send(
            text_data=json.dumps(
                {"message": event["message"], "username": event["username"]}
            )
        )

    # ---- scene control ------------------------------------------------------

    async def _handle_scene_state_set(self, data):
        if not await self._is_gm():
            return  # só GM altera

        new_state = data.get("scene_state")
        if not self._valid_scene_state(new_state):
            return

        # Normaliza character_ids E current_turn_id pra int. Se current_turn_id
        # não está mais na lista (ou é inválido), aponta pro primeiro.
        for s in new_state.get("scenes", []):
            try:
                s["character_ids"] = [int(x) for x in s.get("character_ids", [])]
            except (TypeError, ValueError):
                return
            cur = s.get("current_turn_id")
            try:
                cur_int = int(cur) if cur is not None else None
            except (TypeError, ValueError):
                cur_int = None
            if cur_int is None or cur_int not in s["character_ids"]:
                cur_int = s["character_ids"][0] if s["character_ids"] else None
            s["current_turn_id"] = cur_int

        new_state["version"] = 2
        saved = await self._save_state(new_state)
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "scene_state_changed", "scene_state": saved},
        )

    def _valid_scene_state(self, state):
        if not isinstance(state, dict):
            return False
        scenes = state.get("scenes")
        if not isinstance(scenes, list):
            return False
        if len(scenes) > MAX_SCENES_PER_CAMPAIGN:
            return False
        for s in scenes:
            if not isinstance(s, dict):
                return False
            if not isinstance(s.get("id"), str) or not s["id"]:
                return False
            if not isinstance(s.get("name"), str):
                return False
            if len(s["name"]) > 80:
                return False
            ids = s.get("character_ids", [])
            if not isinstance(ids, list):
                return False
        active_id = state.get("active_scene_id")
        if active_id is not None and not isinstance(active_id, str):
            return False
        return True

    @database_sync_to_async
    def _is_gm(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            return False
        try:
            campanha = Campanha.objects.get(id=self.room_name)
        except (Campanha.DoesNotExist, ValueError):
            return False
        return campanha.dono_id == user.id

    @database_sync_to_async
    def _save_state(self, state):
        campanha = Campanha.objects.get(id=self.room_name)
        campanha.scene_state = state
        campanha.save(update_fields=["scene_state"])
        return state

    async def scene_state_changed(self, event):
        await self.send(
            text_data=json.dumps(
                {"type": "scene_state_changed", "scene_state": event["scene_state"]}
            )
        )

    # ---- ficha rápida (broadcast originado nas views save/delete) ----------

    async def character_created(self, event):
        await self.send(
            text_data=json.dumps(
                {"type": "character_created", "char": event["char"]}
            )
        )

    async def character_deleted(self, event):
        payload = {"type": "character_deleted", "char_id": event["char_id"]}
        if "scene_state" in event:
            payload["scene_state"] = event["scene_state"]
        await self.send(text_data=json.dumps(payload))

    async def character_updated(self, event):
        await self.send(text_data=json.dumps({
            "type": "character_updated",
            "char": event["char"],
        }))

    async def character_vitals_changed(self, event):
        await self.send(text_data=json.dumps({
            "type": "character_vitals_changed",
            "char_id": event["char_id"],
            "hp_atual": event["hp_atual"],
            "hp_max": event["hp_max"],
            "hp_pct": event["hp_pct"],
            "hp_is_negative": event.get("hp_is_negative", False),
            "fp_atual": event["fp_atual"],
            "fp_max": event["fp_max"],
            "fp_pct": event["fp_pct"],
        }))
