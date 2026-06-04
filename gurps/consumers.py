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

        # Identidade autenticada via token assinado (ver _handle_auth).
        # Necessário porque via Cloudflare Tunnel o cookie de sessão NEM SEMPRE
        # chega no upgrade do WebSocket, fazendo o AuthMiddlewareStack resolver
        # AnonymousUser e _is_gm() falhar. O token (vindo do HTTP, que funciona)
        # garante a identidade do GM remoto.
        self.authed_user_id = None
        self.authed_is_gm = False

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

        if msg_type == "auth":
            await self._handle_auth(data)
            return

        if msg_type == "scene_state_set":
            await self._handle_scene_state_set(data)
            return

        if msg_type == "map_grid_config":
            await self._handle_map_grid_config(data)
            return

        if msg_type == "map_switch":
            await self._handle_map_switch(data)
            return

        if msg_type == "map_token_add":
            await self._handle_map_token_add(data)
            return

        if msg_type == "map_token_remove":
            await self._handle_map_token_remove(data)
            return

        if msg_type == "map_token_move":
            await self._handle_map_token_move(data)
            return

        if msg_type == "map_token_update":
            await self._handle_map_token_update(data)
            return

        if msg_type == "map_drawing_add":
            await self._handle_map_drawing_add(data)
            return

        if msg_type == "map_drawing_remove":
            await self._handle_map_drawing_remove(data)
            return

        if msg_type == "map_drawing_clear":
            await self._handle_map_drawing_clear(data)
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
        gm_ok = await self._is_gm()
        if not gm_ok:
            user = self.scope.get("user")
            uname = getattr(user, "username", None) if user else None
            print(f"[WS scene_state_set REJEITADO] room={self.room_name} "
                  f"user={uname!r} — não é GM (ou não autenticado)")
            return  # só GM altera

        new_state = data.get("scene_state")
        if not self._valid_scene_state(new_state):
            print(f"[WS scene_state_set REJEITADO] room={self.room_name} "
                  f"— scene_state inválido")
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

    # ---- map control --------------------------------------------------------

    async def _handle_map_grid_config(self, data):
        if not await self._is_gm():
            return
        asset_id = data.get("asset_id")
        cfg = data.get("config") or {}
        if asset_id is None:
            return
        saved = await self._save_map_grid(int(asset_id), cfg)
        if saved is None:
            return
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "map_state_changed",
             "asset_id": int(asset_id),
             "map_state": saved},
        )

    async def _handle_map_switch(self, data):
        if not await self._is_gm():
            return
        asset_id = data.get("asset_id")
        if asset_id is None:
            return
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "map_switched", "asset_id": int(asset_id)},
        )

    # ---- drawings ---------------------------------------------------------

    async def _handle_map_drawing_add(self, data):
        asset_id = data.get("asset_id")
        drawing = data.get("drawing") or {}
        if asset_id is None:
            return
        saved = await self._add_drawing(int(asset_id), drawing)
        if saved is None:
            return
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "map_drawing_added",
             "asset_id": int(asset_id), "drawing": saved},
        )

    async def _handle_map_drawing_remove(self, data):
        asset_id = data.get("asset_id")
        drawing_id = data.get("drawing_id")
        if asset_id is None or not drawing_id:
            return
        ok = await self._remove_drawing(int(asset_id), drawing_id)
        if not ok:
            return
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "map_drawing_removed",
             "asset_id": int(asset_id), "drawing_id": drawing_id},
        )

    async def _handle_map_drawing_clear(self, data):
        # Limpa TODOS os desenhos do mapa (GM only).
        if not await self._is_gm():
            return
        asset_id = data.get("asset_id")
        if asset_id is None:
            return
        ok = await self._clear_drawings(int(asset_id))
        if not ok:
            return
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "map_drawings_cleared", "asset_id": int(asset_id)},
        )

    @database_sync_to_async
    def _add_drawing(self, asset_id, drawing):
        from gurps.models import MapState, CampanhaAssets
        try:
            asset = CampanhaAssets.objects.get(pk=asset_id)
        except CampanhaAssets.DoesNotExist:
            return None
        if str(asset.campanha_id) != str(self.room_name):
            return None
        ms, _ = MapState.objects.get_or_create(asset=asset)

        import secrets
        author_id = self._effective_user_id()

        kind = drawing.get("kind")
        if kind not in ("line", "rect", "circle", "polygon"):
            return None
        points = drawing.get("points") or []
        if not isinstance(points, list) or not points:
            return None
        # Limpa points: aceita arrays [x, y]; valida tamanho
        try:
            clean_points = [[float(p[0]), float(p[1])] for p in points[:200]]
        except (TypeError, ValueError, IndexError):
            return None

        clean = {
            "id": "drw_" + secrets.token_hex(4),
            "author_id": author_id,
            "author_color": str(drawing.get("author_color", "#3b82f6"))[:20],
            "kind": kind,
            "points": clean_points,
            "stroke_color": str(drawing.get("stroke_color", "#ff0000"))[:20],
            "stroke_width": min(20, max(1, int(drawing.get("stroke_width", 3)))),
            "fill_color": str(drawing.get("fill_color", ""))[:20] or None,
            "layer": drawing.get("layer", "visible"),
        }
        if clean["layer"] not in ("gm_only", "visible", "overlay"):
            clean["layer"] = "visible"
        drawings = list(ms.drawings or [])
        drawings.append(clean)
        # Limita a 500 desenhos por mapa pra não inchar JSON
        if len(drawings) > 500:
            drawings = drawings[-500:]
        ms.drawings = drawings
        ms.version = (ms.version or 0) + 1
        ms.save()
        return clean

    @database_sync_to_async
    def _remove_drawing(self, asset_id, drawing_id):
        from gurps.models import MapState
        ms = MapState.objects.filter(asset_id=asset_id).first()
        if ms is None:
            return False
        if str(ms.asset.campanha_id) != str(self.room_name):
            return False
        uid = self._effective_user_id()
        is_gm = (uid is not None and ms.asset.campanha.dono_id == uid)

        drawings = list(ms.drawings or [])
        target = next((d for d in drawings if d.get("id") == drawing_id), None)
        if target is None:
            return False
        # Owner OR GM
        if not is_gm and target.get("author_id") != uid:
            return False
        ms.drawings = [d for d in drawings if d.get("id") != drawing_id]
        ms.version = (ms.version or 0) + 1
        ms.save()
        return True

    @database_sync_to_async
    def _clear_drawings(self, asset_id):
        from gurps.models import MapState
        ms = MapState.objects.filter(asset_id=asset_id).first()
        if ms is None:
            return False
        if str(ms.asset.campanha_id) != str(self.room_name):
            return False
        ms.drawings = []
        ms.version = (ms.version or 0) + 1
        ms.save()
        return True

    # ---- tokens -----------------------------------------------------------

    async def _handle_map_token_add(self, data):
        if not await self._is_gm():
            return
        asset_id = data.get("asset_id")
        token = data.get("token") or {}
        if asset_id is None:
            return
        saved = await self._add_token(int(asset_id), token)
        if saved is None:
            return
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "map_token_added", "asset_id": int(asset_id), "token": saved},
        )

    async def _handle_map_token_remove(self, data):
        if not await self._is_gm():
            return
        asset_id = data.get("asset_id")
        token_id = data.get("token_id")
        if asset_id is None or not token_id:
            return
        ok = await self._remove_token(int(asset_id), token_id)
        if not ok:
            return
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "map_token_removed",
             "asset_id": int(asset_id),
             "token_id": token_id},
        )

    async def _handle_map_token_move(self, data):
        asset_id = data.get("asset_id")
        token_id = data.get("token_id")
        if asset_id is None or not token_id:
            return
        patch = {}
        for key in ("hex_x", "hex_y", "facing"):
            if key in data:
                patch[key] = data[key]
        if not patch:
            return
        result = await self._update_token(int(asset_id), token_id, patch, check_perm="owner")
        if result is None:
            return
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "map_token_changed",
             "asset_id": int(asset_id),
             "token": result},
        )

    async def _handle_map_token_update(self, data):
        asset_id = data.get("asset_id")
        token_id = data.get("token_id")
        patch = data.get("patch") or {}
        if asset_id is None or not token_id or not patch:
            return
        # Filtra campos que o owner pode editar; GM pode tudo
        result = await self._update_token(int(asset_id), token_id, patch, check_perm="owner")
        if result is None:
            return
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "map_token_changed",
             "asset_id": int(asset_id),
             "token": result},
        )

    @database_sync_to_async
    def _add_token(self, asset_id, token):
        from gurps.models import MapState, CampanhaAssets, CharacterSheetV2, CharacterSheet
        try:
            asset = CampanhaAssets.objects.get(pk=asset_id)
        except CampanhaAssets.DoesNotExist:
            return None
        if str(asset.campanha_id) != str(self.room_name):
            return None
        ms, _ = MapState.objects.get_or_create(asset=asset)
        # Token id gerado server-side pra evitar colisão
        import secrets
        token_id = "tok_" + secrets.token_hex(4)
        layer = token.get("layer", "visible")
        if layer not in ("gm_only", "visible", "overlay"):
            layer = "visible"

        # Se tem character_id, puxa avatar (photo do char ou asset linkado) e
        # cor do owner. Helper compartilhado com a mini (gurps/owner_color.py).
        cid = token.get("character_id")
        image_url = str(token.get("image_url", ""))[:300]
        owner_color = None
        if cid:
            char = CharacterSheetV2.objects.filter(pk=cid).first()
            if char is None:
                char = CharacterSheet.objects.filter(pk=cid).first()
            if char and not image_url:
                # photo do char tem prioridade; senao asset linkado.
                try:
                    if getattr(char, "photo", None) and char.photo and char.photo.url:
                        image_url = char.photo.url
                except (ValueError, AttributeError):
                    pass
                if not image_url:
                    info = getattr(char, "info_campanha", None) or {}
                    linked = info.get("linked_asset_id") or getattr(char, "linked_asset_id", None)
                    if linked:
                        la = CampanhaAssets.objects.filter(pk=int(linked)).first() if str(linked).isdigit() else None
                        if la and la.image:
                            try:
                                image_url = la.image.url
                            except (ValueError, AttributeError):
                                pass
            if char:
                from gurps.owner_color import owner_color_for_character
                owner_color = owner_color_for_character(char, asset.campanha)

        clean = {
            "id": token_id,
            "character_id": cid,
            "label": str(token.get("label", ""))[:80],
            "image_url": image_url,
            "color": owner_color or str(token.get("color", "#c9a55c"))[:20],
            "hex_x": int(token.get("hex_x", 0)),
            "hex_y": int(token.get("hex_y", 0)),
            "facing": int(token.get("facing", 0)) % 6,
            "size_modifier": int(token.get("size_modifier", 0)),
            "size_scale": float(token.get("size_scale", 1.0)),  # multiplicador do raio
            "posture": token.get("posture", "standing"),
            "status_effects": list(token.get("status_effects", [])),
            "z_index": int(token.get("z_index", 1)),
            "layer": layer,
        }
        tokens = list(ms.tokens or [])
        tokens.append(clean)
        ms.tokens = tokens
        ms.version = (ms.version or 0) + 1
        ms.save()
        return clean

    @database_sync_to_async
    def _remove_token(self, asset_id, token_id):
        from gurps.models import MapState
        ms = MapState.objects.filter(asset_id=asset_id).first()
        if ms is None:
            return False
        if str(ms.asset.campanha_id) != str(self.room_name):
            return False
        before = len(ms.tokens or [])
        ms.tokens = [t for t in (ms.tokens or []) if t.get("id") != token_id]
        if len(ms.tokens) == before:
            return False
        ms.version = (ms.version or 0) + 1
        ms.save()
        return True

    @database_sync_to_async
    def _update_token(self, asset_id, token_id, patch, check_perm):
        from gurps.models import MapState, CharacterSheetV2, CharacterSheet
        ms = MapState.objects.filter(asset_id=asset_id).first()
        if ms is None:
            return None
        if str(ms.asset.campanha_id) != str(self.room_name):
            return None
        uid = self._effective_user_id()
        is_gm = (uid is not None and ms.asset.campanha.dono_id == uid)

        tokens = list(ms.tokens or [])
        target = None
        for t in tokens:
            if t.get("id") == token_id:
                target = t
                break
        if target is None:
            return None

        # Permission: owner do char OU GM
        if check_perm == "owner" and not is_gm:
            cid = target.get("character_id")
            owner_id = None
            if cid:
                v2 = CharacterSheetV2.objects.filter(pk=cid).first()
                if v2:
                    owner_id = v2.owner_id
                else:
                    v1 = CharacterSheet.objects.filter(pk=cid).first()
                    if v1:
                        # V1 nao tem owner FK; usa info_campanha.player_name
                        from gurps.models import RegisterUser
                        owner_name = (v1.info_campanha or {}).get("player_name")
                        if owner_name:
                            owner = RegisterUser.objects.filter(username=owner_name).first()
                            owner_id = owner.id if owner else None
            if owner_id != uid:
                return None  # nao pode

        # Apply patch (filtra campos permitidos)
        ALLOWED_ANY = {"hex_x", "hex_y", "facing", "posture", "status_effects",
                       "label", "color", "z_index", "size_scale"}
        ALLOWED_GM_ONLY = {"layer"}  # só GM muda camada do token
        for k, v in patch.items():
            if k in ALLOWED_GM_ONLY and not is_gm:
                continue
            if k not in ALLOWED_ANY and k not in ALLOWED_GM_ONLY:
                continue
            if k == "facing":
                target[k] = int(v) % 6
            elif k in ("hex_x", "hex_y", "z_index"):
                target[k] = int(v)
            elif k == "status_effects":
                target[k] = list(v)
            elif k == "size_scale":
                try:
                    target[k] = max(0.3, min(5.0, float(v)))
                except (TypeError, ValueError):
                    pass
            elif k == "layer":
                if v in ("gm_only", "visible", "overlay"):
                    target[k] = v
            else:
                target[k] = v

        ms.tokens = tokens
        ms.version = (ms.version or 0) + 1
        ms.save()
        return target

    @database_sync_to_async
    def _save_map_grid(self, asset_id, cfg):
        # Grid config agora vive na Campanha (compartilhado entre todos os
        # mapas). asset_id ainda recebemos pra compat mas usamos pra achar
        # a Campanha; o salvar e a leitura usam Campanha.
        from gurps.models import Campanha, CampanhaAssets
        try:
            asset = CampanhaAssets.objects.get(pk=asset_id)
        except CampanhaAssets.DoesNotExist:
            return None
        if str(asset.campanha_id) != str(self.room_name):
            return None
        c = asset.campanha
        if "enabled" in cfg:
            c.grid_enabled = bool(cfg["enabled"])
        if "size_px" in cfg:
            c.grid_size_px = max(8, int(cfg["size_px"]))
        if "offset_x" in cfg:
            c.grid_offset_x = int(cfg["offset_x"])
        if "offset_y" in cfg:
            c.grid_offset_y = int(cfg["offset_y"])
        if "color" in cfg:
            c.grid_color = str(cfg["color"])[:20]
        if "opacity" in cfg:
            try:
                c.grid_opacity = float(cfg["opacity"])
            except (TypeError, ValueError):
                pass
        c.save(update_fields=[
            "grid_enabled", "grid_size_px", "grid_offset_x",
            "grid_offset_y", "grid_color", "grid_opacity"
        ])
        return {
            "asset_id": asset_id,
            "grid_enabled": c.grid_enabled,
            "grid_size_px": c.grid_size_px,
            "grid_offset_x": c.grid_offset_x,
            "grid_offset_y": c.grid_offset_y,
            "grid_color": c.grid_color,
            "grid_opacity": c.grid_opacity,
        }

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

    # ---- auth via token assinado (resiliente a falha de cookie no tunnel) ----

    async def _handle_auth(self, data):
        """Cliente envia {type:'auth', token:'...'} logo após conectar.
        O token é gerado no HTTP (django.core.signing) e codifica (uid, cid).
        Valida assinatura + que cid bate com a sala + se o user é dono → GM.
        """
        token = data.get("token")
        if not token:
            return
        payload = await self._resolve_ws_token(token)
        if not payload:
            return
        if str(payload.get("cid")) != str(self.room_name):
            return
        self.authed_user_id = payload.get("uid")
        self.authed_is_gm = await self._check_is_dono(self.authed_user_id)

    @database_sync_to_async
    def _resolve_ws_token(self, token):
        from django.core import signing
        try:
            return signing.loads(token, salt="rd6-ws-auth", max_age=60 * 60 * 24 * 7)
        except signing.BadSignature:
            return None

    @database_sync_to_async
    def _check_is_dono(self, uid):
        if uid is None:
            return False
        campanha = Campanha.objects.filter(id=self.room_name).first()
        return bool(campanha and campanha.dono_id == uid)

    def _effective_user_id(self):
        """ID do user confiável: token assinado tem prioridade; senão scope."""
        if self.authed_user_id is not None:
            return self.authed_user_id
        user = self.scope.get("user")
        if user and getattr(user, "is_authenticated", False):
            return user.id
        return None

    async def _is_gm(self):
        # Token assinado (vindo do HTTP) tem prioridade — funciona via tunnel.
        if self.authed_is_gm:
            return True
        return await self._is_gm_via_scope()

    @database_sync_to_async
    def _is_gm_via_scope(self):
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

    async def map_state_changed(self, event):
        await self.send(text_data=json.dumps({
            "type": "map_state_changed",
            "asset_id": event["asset_id"],
            "map_state": event["map_state"],
        }))

    async def map_switched(self, event):
        await self.send(text_data=json.dumps({
            "type": "map_switched",
            "asset_id": event["asset_id"],
        }))

    async def map_token_added(self, event):
        await self.send(text_data=json.dumps({
            "type": "map_token_added",
            "asset_id": event["asset_id"],
            "token": event["token"],
        }))

    async def map_token_removed(self, event):
        await self.send(text_data=json.dumps({
            "type": "map_token_removed",
            "asset_id": event["asset_id"],
            "token_id": event["token_id"],
        }))

    async def map_token_changed(self, event):
        await self.send(text_data=json.dumps({
            "type": "map_token_changed",
            "asset_id": event["asset_id"],
            "token": event["token"],
        }))

    async def map_drawing_added(self, event):
        await self.send(text_data=json.dumps({
            "type": "map_drawing_added",
            "asset_id": event["asset_id"],
            "drawing": event["drawing"],
        }))

    async def map_drawing_removed(self, event):
        await self.send(text_data=json.dumps({
            "type": "map_drawing_removed",
            "asset_id": event["asset_id"],
            "drawing_id": event["drawing_id"],
        }))

    async def map_drawings_cleared(self, event):
        await self.send(text_data=json.dumps({
            "type": "map_drawings_cleared",
            "asset_id": event["asset_id"],
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
