import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from gurps.models import Campanha, CampanhaAssets, Message, CharacterSheet, CharacterSheetV2
from django.contrib.auth.decorators import login_required
from django.contrib import auth
import random


# =============================================================================
# Adapters V2 → shape compatível V1 (pra templates legados continuarem lendo)
# =============================================================================

def _wrap_v2_as_legacy(v2):
    """Adiciona atributos lookalike V1 no instance V2 pro template legado.

    O template antigo (interface_jogo.html) lê:
      - personagem.atributos.ST / DX / IQ / HT  (em CAPS)
      - personagem.sub_attributes.hp / fp / will / perception / basic_lift
        / swing / thrust / speed / move / dodge / parry_unarmed / etc.
      - personagem.skills[].nome / .nh
      - personagem.maneuvers_*[].nome / .nh / .damage / .detalhes
      - personagem.equipment_*[].nome / .damage / .reach / .parry / .cost / .weight

    Como o schema V2 usa keys em inglês minúsculas, aplicamos aliases pra
    manter compat sem reescrever o template inteiro.
    Idempotente: chamar 2× não quebra.
    """
    from gurps.sheet_v2_calc import compute_secondary

    if getattr(v2, "_wrapped_legacy", False):
        return v2

    primary = v2.primary_attributes or {}
    sec = compute_secondary(primary, v2.secondary_modifiers or {})

    st, dx, iq, ht = primary.get("st", 10), primary.get("dx", 10), primary.get("iq", 10), primary.get("ht", 10)

    # Atributos: template lê em CAPS
    v2.atributos = {
        "ST": st, "DX": dx, "IQ": iq, "HT": ht,
        "st": st, "dx": dx, "iq": iq, "ht": ht,  # também minúsculas (compat)
    }
    # Secundárias: template lê várias keys; mapeamos todas que conseguimos
    v2.sub_attributes = {
        "hp": sec["hp"],
        "fp": sec["fp"],
        "will": sec["will"],
        "per": sec["per"],
        "perception": sec["per"],          # alias usado no template
        "speed": sec["basic_speed"],
        "move": sec["basic_move"],
        "dodge": sec["dodge"],
        "basic_lift": sec["basic_lift"],
        "thrust": sec["thrust"],
        "swing": sec["swing"],
        "thrust_weapon": "",               # template lê mas não temos cálculo automático
        "swing_weapon": "",
        "parry_unarmed": (dx // 2) + 3,    # GURPS default parry
        "parry_weapon": "",
        "stress": "",
        "Jump": "",                        # capital J — template legacy quirk
    }
    v2.info_campanha = {
        "player_name": v2.owner.username if v2.owner else "",
        "nome_campanha": v2.campanha.nome if v2.campanha else "",
        "nome_gm": v2.campanha.dono.username if v2.campanha and v2.campanha.dono else "",
        "is_quick_npc": v2.is_quick_npc,
        # Asset linkado (avatar da ficha rápida) vive em runtime_stats na V2.
        # Copia pro info_campanha pra _resolve_avatar_url achar após reload.
        "linked_asset_id": (v2.runtime_stats or {}).get("linked_asset_id"),
    }
    pts = v2.points or {}
    v2.pontos_soma = {
        "total": pts.get("available", 150),
        "spent": pts.get("spent", 0),
        "remaining": pts.get("remaining", 0),
    }

    # Skills: template usa skill.nome + skill.nh — aliases sobre label + computed_level
    def _alias_skill(s):
        out = dict(s)
        out.setdefault("nome", s.get("label", s.get("id", "")))
        out.setdefault("nh", s.get("computed_level"))
        return out
    v2.skills = [_alias_skill(s) for s in (v2.skills or [])]

    # Maneuvers: template usa nome/nh/damage/detalhes — aliases sobre name/details
    def _alias_maneuver(m):
        out = dict(m)
        out.setdefault("nome", m.get("name", ""))
        out.setdefault("detalhes", m.get("details", ""))
        return out
    v2.maneuvers_melee = [_alias_maneuver(m) for m in (v2.maneuvers_melee or [])]
    v2.maneuvers_ranged = [_alias_maneuver(m) for m in (v2.maneuvers_ranged or [])]
    v2.maneuvers_defense = [_alias_maneuver(m) for m in (v2.maneuvers_defense or [])]

    # Equipment: template usa equip.nome / damage / reach / parry / cost / weight
    def _alias_equip(e):
        out = dict(e)
        out.setdefault("nome", e.get("name", ""))
        out.setdefault("reach", e.get("reach", ""))
        out.setdefault("parry", e.get("parry", ""))
        out.setdefault("cost", e.get("cost", ""))
        out.setdefault("weight", e.get("weight", ""))
        out.setdefault("damage", e.get("damage", ""))
        out.setdefault("dr", e.get("dr", ""))
        out.setdefault("location", e.get("location", ""))
        return out
    v2.equipment_melee = [_alias_equip(e) for e in (v2.equipment_melee or [])]
    v2.equipment_ranged = [_alias_equip(e) for e in (v2.equipment_ranged or [])]
    v2.equipment_armor = [_alias_equip(e) for e in (v2.equipment_armor or [])]
    v2.equipment_misc = [_alias_equip(e) for e in (v2.equipment_misc or [])]

    # Advantages / Disadvantages: template legado pode iterar exibindo .nome
    def _alias_adv(a):
        out = dict(a)
        out.setdefault("nome", a.get("label", a.get("id", "")))
        out.setdefault("custo", a.get("computed_cost", 0))
        return out
    v2.advantages = [_alias_adv(a) for a in (v2.advantages or [])]
    v2.disadvantages = [_alias_adv(d) for d in (v2.disadvantages or [])]

    v2._wrapped_legacy = True
    return v2


def _get_player_sheets_v2_then_v1(campanha, username):
    """Retorna lista de fichas do player na campanha, V2 primeiro, V1 fallback.

    Se o user tem V2 nesta campanha, usa as V2 (com wrapper compat).
    Senão, usa V1.
    """
    v2_qs = CharacterSheetV2.objects.filter(
        campanha=campanha, owner__username=username
    ).order_by("-id")

    if v2_qs.exists():
        return [_wrap_v2_as_legacy(f) for f in v2_qs]

    # Fallback: V1
    return list(
        CharacterSheet.objects.filter(
            info_campanha__nome_campanha=campanha.nome,
            info_campanha__player_name=username,
        ).order_by("-id")
    )


def _get_all_sheets_for_campanha(campanha):
    """Todas as fichas da campanha (todos os players). V2 + V1 que não foram migradas."""
    v2_list = [_wrap_v2_as_legacy(f) for f in
               CharacterSheetV2.objects.filter(campanha=campanha).order_by("-id")]
    # Owners que já têm V2 — V1 desses owners é omitida
    owners_v2 = {f.owner_id for f in v2_list if f.owner_id}
    v1_list = []
    for f in CharacterSheet.objects.filter(info_campanha__nome_campanha=campanha.nome).order_by("-id"):
        owner_name = (f.info_campanha or {}).get("player_name")
        if owner_name:
            # Busca user_id; se já tem V2 do mesmo owner, pula
            from gurps.models import RegisterUser
            owner = RegisterUser.objects.filter(username=owner_name).first()
            if owner and owner.id in owners_v2:
                continue
        v1_list.append(f)
    return v2_list + v1_list


def _safe_int(value, default=0):
    """Converte para int tolerando strings, vírgula decimal e None."""
    if value is None:
        return default
    try:
        return int(str(value).strip().replace(",", "."))
    except (TypeError, ValueError):
        try:
            return int(float(str(value).strip().replace(",", ".")))
        except (TypeError, ValueError):
            return default


def _safe_float(value, default=0.0):
    """Converte para float tolerando strings, vírgula decimal e None."""
    if value is None:
        return default
    try:
        return float(str(value).strip().replace(",", "."))
    except (TypeError, ValueError):
        return default


def _migrate_scene_state(raw):
    """Migra estrutura antiga ({active: {present_character_ids}}) pra v2 multi-cena."""
    if not raw:
        return {"version": 2, "scenes": [], "active_scene_id": None}
    if raw.get("version") == 2:
        return raw
    active_old = raw.get("active") or {}
    char_ids = active_old.get("order") or active_old.get("present_character_ids") or []
    if not char_ids:
        return {"version": 2, "scenes": [], "active_scene_id": None}
    scene = {
        "id": "s_001",
        "name": active_old.get("name") or "Cena 1",
        "character_ids": list(char_ids),
    }
    return {"version": 2, "scenes": [scene], "active_scene_id": "s_001"}


def _light_scene_state_for_client(state):
    """scene_state enxuto pro cliente: sem os campos pesados (tokens/drawings/
    char_runtime) que o RD6_SCENE_STATE não usa. Mantém metadados das cenas."""
    if not isinstance(state, dict):
        return {"version": 2, "scenes": [], "active_scene_id": None}
    light = []
    for s in state.get("scenes") or []:
        if not isinstance(s, dict):
            continue
        light.append({
            "id": s.get("id"),
            "name": s.get("name"),
            "character_ids": s.get("character_ids", []),
            "current_turn_id": s.get("current_turn_id"),
            "background_asset_id": s.get("background_asset_id"),
        })
    return {
        "version": state.get("version", 2),
        "active_scene_id": state.get("active_scene_id"),
        "scenes": light,
    }


def _resolve_avatar_url(character):
    """Avatar: photo do char se houver, senão image do asset linkado, senão None.

    Funciona pra V1 (info_campanha.linked_asset_id) e V2 (wrapper já populou
    info_campanha; quick NPC V2 pode ter linked_asset_id direto no objeto).
    """
    if character.photo:
        try:
            return character.photo.url
        except Exception:
            pass
    info = getattr(character, "info_campanha", None) or {}
    # linked_asset_id pode estar em info_campanha (V1), como atributo direto, ou
    # em runtime_stats (ficha rápida V2 crua, sem wrapper).
    linked = (info.get("linked_asset_id")
              or getattr(character, "linked_asset_id", None)
              or (getattr(character, "runtime_stats", None) or {}).get("linked_asset_id"))
    if linked:
        try:
            asset = CampanhaAssets.objects.get(id=int(linked))
            if asset.image:
                return asset.image.url
        except (CampanhaAssets.DoesNotExist, ValueError, TypeError):
            pass
    return None


def _hp_pct_and_negative(hp_atual, hp_max):
    """Calcula percentual da barra de HP + flag is_negative.

    HP >= 0 → pct = HP/hp_max (barra vermelha enche de 0 → 100%)
    HP <  0 → pct = abs(HP) / (10×hp_max) (barra roxa enche de 0 → 100%,
              representando 0 → -10×hp_max). Clampa em 100%.
    """
    if hp_max <= 0:
        return "0", False
    if hp_atual >= 0:
        return f"{100 * hp_atual / hp_max:.1f}", False
    neg_cap = 10 * hp_max
    abs_hp = min(abs(hp_atual), neg_cap)
    return f"{100 * abs_hp / neg_cap:.1f}", True


def _build_player_mini(character, present_ids=None, show_numbers=False, campanha=None,
                       color_map=None, runtime_override=None):
    """Empacota a ficha num dicionário leve pra exibição da barra de players.

    ``show_numbers`` controla privacidade: True → mostra ``HP X/Y`` e ``FP X/Y``
    em texto sobre a barra; False → só a barra colorida sem os valores. GM
    sempre tem show_numbers=True; players têm True só na própria ficha.

    ``campanha`` (opcional) é usado pra resolver a cor identitária do dono
    (borda da mini). GM = vermelho; players = HSL do username.

    ``runtime_override`` (opcional): quando a campanha usa cenas, HP/FP/status
    vêm do estado DAQUELA cena (scene['char_runtime'][char_id]), não do
    runtime_stats global do model. Passe um dict (mesmo vazio = full) pra ativar
    o modo-cena; None = usa o runtime_stats global (comportamento legado).
    """
    sub = character.sub_attributes or {}
    runtime = runtime_override if runtime_override is not None else (character.runtime_stats or {})
    hp_max = _safe_int(sub.get("hp"))
    fp_max = _safe_int(sub.get("fp"))
    hp_atual = _safe_int(runtime.get("hp_atual"), default=hp_max)
    fp_atual = _safe_int(runtime.get("fp_atual"), default=fp_max)
    speed = _safe_float(sub.get("speed"))
    nome = character.nome_personagem or "?"
    initials = ("".join(w[0] for w in nome.split()[:2]) or "?").upper()
    hp_pct, hp_is_negative = _hp_pct_and_negative(hp_atual, hp_max)
    fp_pct = f"{100 * fp_atual / fp_max:.1f}" if fp_max > 0 else "0"
    is_present = present_ids is None or character.id in present_ids
    info = character.info_campanha or {}

    # Cor do dono (borda do avatar). GM=vermelho, players=cor única.
    owner_color = "#c9a55c"
    if campanha is not None:
        try:
            from gurps.owner_color import color_for_character
            owner_color = color_for_character(character, campanha, color_map=color_map)
        except Exception:
            pass

    # Status effects persistentes (runtime_stats.status_effects = lista de chaves)
    status_effects = list(runtime.get("status_effects") or [])

    return {
        "id": character.id,
        "nome": nome,
        "initials": initials,
        "avatar_url": _resolve_avatar_url(character),
        "hp_atual": hp_atual,
        "hp_max": hp_max,
        "hp_pct": hp_pct,
        "hp_is_negative": hp_is_negative,
        "fp_atual": fp_atual,
        "fp_max": fp_max,
        "fp_pct": fp_pct,
        "speed": speed,
        "is_present": is_present,
        "show_numbers": show_numbers,
        "is_quick_npc": bool(info.get("is_quick_npc")),
        "owner_color": owner_color,
        "status_effects": status_effects,
    }


@login_required(login_url="gurps:login")
def game_interface(request, campanha_id, slot):
    username = request.user.username
    campanha = get_object_or_404(Campanha, id=campanha_id)
    # ===== A CENA dirige o mapa: fundo + tokens + desenhos + vida =====
    # O save state vive na CENA (scene_state). O mapa é só um fundo: branco OU
    # a imagem de um asset enviado (que fica intacto e nunca guarda estado).
    scene_state = _migrate_scene_state(campanha.scene_state)
    scenes = scene_state.get("scenes") or []
    active_scene_id = scene_state.get("active_scene_id")
    active_scene = next((s for s in scenes if s.get("id") == active_scene_id), None)
    if active_scene is None and scenes:
        active_scene = scenes[0]
        scene_state["active_scene_id"] = active_scene["id"]

    _is_user_gm = (campanha.dono_id == request.user.id)

    # NÃO deletar slot=3 aqui. O slot=3 já foi usado por DUAS coisas conflitantes:
    # (a) mapas-de-cena em branco vestigiais e (b) assets com show=False (convenção
    # antiga do add/edit_asset). Deletar slot=3 apagava assets ocultos do GM.
    # Agora a visibilidade é SÓ o campo `show`; slot=3 foi descontinuado.

    # Fundo da cena ativa: asset enviado (imagem) ou branco (sem asset).
    bg_asset = None
    if active_scene and active_scene.get("background_asset_id"):
        bg_asset = CampanhaAssets.objects.filter(
            pk=active_scene["background_asset_id"], campanha=campanha
        ).first()
    if bg_asset is not None:
        pagina_inicial = bg_asset
        map_image_url = bg_asset.image.url if bg_asset.image else ""
    else:
        # Placeholder estrutural pro template (.id). Imagem vazia = branco quando
        # há cena ativa; sem cena nenhuma, mostra a imagem default da campanha.
        pagina_inicial = get_object_or_404(CampanhaAssets, campanha=campanha, slot=slot)
        if active_scene is not None:
            map_image_url = ""
        else:
            map_image_url = pagina_inicial.image.url if pagina_inicial.image else ""

    # MapState do asset estrutural: só pra data-map-state + soft-migrate do grid
    # (tokens/desenhos NÃO vêm mais daqui — vêm da cena).
    from gurps.models import MapState as _MapState
    map_state, _created = _MapState.objects.get_or_create(asset=pagina_inicial)
    if _created is False and not campanha.grid_enabled and map_state.grid_enabled:
        campanha.grid_enabled = map_state.grid_enabled
        campanha.grid_size_px = map_state.grid_size_px
        campanha.grid_offset_x = map_state.grid_offset_x
        campanha.grid_offset_y = map_state.grid_offset_y
        campanha.grid_color = map_state.grid_color
        campanha.grid_opacity = map_state.grid_opacity
        campanha.save(update_fields=[
            "grid_enabled", "grid_size_px", "grid_offset_x",
            "grid_offset_y", "grid_color", "grid_opacity"
        ])

    # Tokens/desenhos vêm da CENA ATIVA. Filtra gm_only pra quem não é GM.
    scene_tokens = (active_scene.get("tokens") if active_scene else None) or []
    scene_drawings = (active_scene.get("drawings") if active_scene else None) or []
    if _is_user_gm:
        visible_tokens = scene_tokens
        visible_drawings = scene_drawings
    else:
        visible_tokens = [t for t in scene_tokens
                          if t.get("layer", "visible") != "gm_only"]
        visible_drawings = [d for d in scene_drawings
                            if d.get("layer", "visible") != "gm_only"]
    messages = Message.objects.filter(campanha=campanha).order_by("timestamp")
    assets = CampanhaAssets.objects.filter(
        campanha=campanha, slot__in=[1, 2], show=True
    ).order_by("-id")
    # Journal do GM vê TODOS os assets slot 1/2, inclusive os com show=False
    # (bug antigo: o GM só via show=True dentro do jogo). Players seguem com
    # `assets` (show=True). Exclui slot 3 (mapas-de-cena em branco vestigiais).
    assets_gm = CampanhaAssets.objects.filter(
        campanha=campanha, slot__in=[1, 2]
    ).order_by("-id")
    # Lista completa dos assets pro GM linkar fichas rápidas a (visíveis ou não).
    # Exclui os mapas-de-cena auto-criados (slot 3, em branco) pra não poluir
    # o seletor manual "Trocar mapa ativo" — esses são trocados pelas cenas.
    all_assets_for_gm = list(
        CampanhaAssets.objects.filter(campanha=campanha)
        .exclude(slot=3)
        .order_by("-id").values("id", "name")
    )

    print(f"\n Aqui estão os assets {assets} \n")

    def definir_cor(message_content):
        msg_lower = message_content.lower().strip()
        if msg_lower.endswith("acerto"):
            return "bg-green"
        elif msg_lower.endswith("falha"):
            return "bg-gray"
        elif msg_lower.endswith("sucesso"):
            return "bg-purple"
        elif msg_lower.endswith("erro crítico"):
            return "bg-red"
        elif msg_lower.endswith("sucesso decisivo"):
            return "bg-orange"
        return "bg-blue"

    messages_with_colors = [
        {"message": msg, "color": definir_cor(msg.content)} for msg in messages
    ]

    # ========== Fichas do player na campanha (V2 com fallback V1) ==========
    # `personagens_gm` é só nomenclatura legada — na verdade são as fichas
    # DO próprio user (mesmo se ele é GM).
    fichas_do_player = _get_player_sheets_v2_then_v1(campanha, request.user.username)

    # Permite trocar entre fichas do player via ?character=<id>. Se vier um id
    # válido, ele vira o "ativo" e a lista é rotacionada pra deixá-lo na frente.
    requested_id = request.GET.get("character")
    if requested_id and fichas_do_player:
        try:
            req_id = int(requested_id)
            idx = next((i for i, f in enumerate(fichas_do_player) if f.id == req_id), None)
            if idx is not None and idx != 0:
                fichas_do_player = fichas_do_player[idx:] + fichas_do_player[:idx]
        except (TypeError, ValueError):
            pass

    personagem = fichas_do_player[0] if fichas_do_player else None
    personagens_gm = fichas_do_player  # alias compat

    # ID do próximo personagem pra botão "→" da side nav (None se 0 ou 1 ficha).
    next_character_id = fichas_do_player[1].id if len(fichas_do_player) > 1 else None

    # Todas as fichas da campanha (todos players + GM) — V2 + V1 fallback
    personagens_journal = _get_all_sheets_for_campanha(campanha)
    # Avatar do journal: foto do char OU imagem do asset linkado (ficha rápida).
    # Sem isso, quick NPCs (photo vazio, mas com linked_asset_id) apareciam
    # como "sem imagem" no journal mesmo tendo retrato no asset linkado.
    for _p in personagens_journal:
        _p.avatar_url = _resolve_avatar_url(_p)

    # sheet_list = fichas secundárias do player (sem a "primária" #1)
    if len(fichas_do_player) > 1:
        sheet_list = fichas_do_player[1:]
    else:
        sheet_list = []
    print(f"\nFICHAS DO PLAYER ({username}): {len(fichas_do_player)}\n")
    # active_scene / scene_state já resolvidos no topo (dirigem fundo+estado).
    # Personagens "em cena" e ordem vêm da cena ativa. Sem cena → todos presentes.
    if active_scene:
        order_ids = active_scene.get("character_ids") or []
        present_ids = set(order_ids)
    else:
        order_ids = []
        present_ids = None

    from django.conf import settings as dj_settings

    is_gm = _is_user_gm

    # Token assinado pra autenticar o WebSocket de forma confiável mesmo quando
    # o cookie de sessão não chega no upgrade do WS (via Cloudflare Tunnel).
    # O cliente envia {type:'auth', token} logo após conectar. Ver consumers.py.
    from django.core import signing
    ws_token = signing.dumps(
        {"uid": request.user.id, "cid": campanha.id},
        salt="rd6-ws-auth",
    )

    # Minis de todos os personagens da campanha (privacidade aplicada).
    # Mapa de cores distintas por player (golden angle). Computado uma vez.
    from gurps.owner_color import build_player_color_map
    player_color_map = build_player_color_map(personagens_journal, campanha)

    # Vida/status por CENA: com cena ativa, HP/FP/status vêm de
    # active_scene['char_runtime'] (ausente = full); sem cena, runtime_stats global.
    scene_runtime = (active_scene.get("char_runtime") or {}) if active_scene else None

    players_minis = []
    for p in personagens_journal:
        owner = (p.info_campanha or {}).get("player_name")
        show_numbers = is_gm or (owner == username)
        override = scene_runtime.get(str(p.id), {}) if scene_runtime is not None else None
        players_minis.append(_build_player_mini(p, present_ids, show_numbers,
                                                campanha=campanha,
                                                color_map=player_color_map,
                                                runtime_override=override))

    # Ordena minis pela ordem manual da cena ativa. Quem não está na cena fica
    # no fim em ordem alfabética (só importa pro modal — não aparece na barra).
    if order_ids:
        order_map = {pid: i for i, pid in enumerate(order_ids)}
        players_minis.sort(
            key=lambda p: (0, order_map[p["id"]]) if p["id"] in order_map else (1, p["nome"].lower())
        )

    context = {
        "personagem": personagem,
        "personagens_gm": personagens_gm,
        "campanha": campanha,
        "pagina_inicial": pagina_inicial,
        "messages": messages_with_colors,  # Enviamos as mensagens com cor ao template
        "username": username,
        "assets": assets,
        "assets_gm": assets_gm,
        "personagens_journal": personagens_journal,
        "sheet_list": sheet_list,
        "next_character_id": next_character_id,
        "map_state": map_state,
        "map_image_url": map_image_url,
        "map_tokens": visible_tokens,
        "map_drawings": visible_drawings,
        "players_minis": players_minis,
        "is_gm": is_gm,
        "ws_token": ws_token,
        "scene_state": _light_scene_state_for_client(scene_state),
        "all_characters_data": [
            {"id": p["id"], "nome": p["nome"], "speed": p["speed"], "is_quick_npc": p["is_quick_npc"]} for p in players_minis
        ],
        "all_assets_for_gm": all_assets_for_gm,
        "active_background_id": active_scene.get("background_asset_id") if active_scene else None,
        # IDs das fichas do próprio player — pra liberar mover o próprio token
        # no client (o server revalida por owner de qualquer jeito).
        "owned_char_ids": [f.id for f in fichas_do_player],
        "debug": dj_settings.DEBUG,
    }
    return render(request, "global/interface_jogo.html", context)


@login_required(login_url="gurps:login")
def leave_game(request):
    username = request.user.username
    print(f"\n  O USUÁRIO [{username}] CLICOU EM LEAVE GAME\n")
    return redirect("gurps:index")


@csrf_exempt
def save_message(request):
    if request.method == "POST":
        data = json.loads(request.body)
        message_content = data.get("message")
        campanha_id = data.get("campanha_id")
        user = request.user

        if message_content and campanha_id:
            print(f"\nMensagem: {message_content}\n")
            campanha = get_object_or_404(Campanha, id=campanha_id)
            Message.objects.create(
                user=user,
                campanha=campanha,
                content=message_content,
            )
            return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=400)


def roll_d6(quantidade: int) -> int:
    """Rola uma quantidade de dados de 6 lados e aplica um incremento."""
    print(f"\nquantidade de dados: {quantidade}\n")
    resultado = sum(random.randint(1, 6) for _ in range(quantidade))
    print(f"\nRESULTADO: {resultado}\n")
    return resultado


def roll_d6_interface(request, quantidade: int, inc: str):
    """Rola uma quantidade de dados de 6 lados e aplica um incremento."""
    inc = float(inc)  # Converte o incremento para float

    print(f"\nquantidade de dados: {quantidade}\n")
    resultado = sum(random.randint(1, 6) for _ in range(quantidade)) + inc
    print(f"\nRESULTADO: {resultado}\n")
    return JsonResponse({"resultado": resultado})


def verify_roll(nh: int, roll: int, bonus: int, redutor: int) -> str:
    """Verifica se o resultado de um teste de habilidade foi um sucesso ou falha."""
    nh_final = nh + bonus - redutor
    result = nh_final - roll
    print(
        f"\nVERIFY_ROLL:\nNH: {nh},NH_final:{nh_final} ROLL: {roll}, RESULT: {result}\n"
    )

    if roll == 18:
        print(f"Motivo: ROLL == 18")
        message = "ERRO CRÍTICO"
        return message

    elif roll == 3:
        print(f"Motivo: ROLL == 3")
        message = "SUCESSO DECISIVO"
        return message

    elif roll == 4:
        print(f"Motivo: ROLL == 4")
        message = "SUCESSO"
        return message

    elif roll == 5 and nh_final >= 15:
        print(f"Motivo: ROLL == 5")
        message = "SUCESSO"
        return message

    elif roll == 6 and nh_final >= 16:
        print(f"Motivo: ROLL == 6")
        message = "SUCESSO"
        return message

    elif roll > 14 and nh_final < 7:
        print(f"Diferença de 10")
        message = "ERRO CRÍTICO"
        return message

    elif roll == 17:
        print(f"Motivo: ROLL == 17")
        message = "Falha"
        return message

    elif result >= 0:
        print(f"Motivo: RESULT >= 0")
        message = "Acerto"
        return message

    elif result < 0:
        print(f"Motivo: RESULT < 0")
        message = "Falha"
        return message


def roll_test_attribute(
    request, atributo: str, nh_attribute: int, bonus: int, redutor: int, name: str
):
    roll = roll_d6(3)
    message = verify_roll(nh_attribute, roll, bonus, redutor)
    nh_final = nh_attribute + bonus - redutor
    print(
        f"\nATRIBUTO: {atributo}  NH: {nh_attribute}, NH_FINAL:{nh_final}ROLL: {roll}, MESSAGE: {message}\n"
    )

    return JsonResponse(
        {
            "atributo": atributo,
            "roll": roll,
            "nh": nh_attribute,
            "nh_final": nh_final,
            "message": message,
            "nome_personagem": name,
        }
    )


def roll_test_attack(
    request,
    atributo: str,
    nh_attribute: int,
    bonus: int,
    redutor: int,
    dmg: str,
    name: str,
):
    print(f"\nDANO: {dmg}\n")

    # Divide a string em partes
    qtd_dices = int(dmg.split("d")[0])
    parts = dmg.split("d6")

    # Verifica se há um incremento (exemplo: "+1" ou "-2") e converte para inteiro, caso contrário, assume 0
    inc = int(parts[1]) if len(parts) > 1 and parts[1] else 0

    print(f"\nQUANTIDADE DE DADOS: {qtd_dices} com incremento de : {inc}\n")

    roll = roll_d6(3)
    message = verify_roll(nh_attribute, roll, bonus, redutor)
    nh_final = nh_attribute + bonus - redutor
    roll_dmg = roll_d6(qtd_dices)
    dano_final = roll_dmg + inc  # Usa 'inc' que já está tratado

    print(
        f"\nNOME:{name}\nATRIBUTO: {atributo}\nNH: {nh_attribute}\nNH_FINAL:{nh_final}\nROLL: {roll}\nROLL DMG:{roll_dmg}\nDMG:{dano_final}\nMESSAGE: {message}\n\n"
    )

    return JsonResponse(
        {
            "atributo": atributo,
            "roll": roll,
            "nh": nh_attribute,
            "nh_final": nh_final,
            "message": message,
            "damage": dano_final,
            "nome_personagem": name,
        }
    )


def get_character_gm(request):
    """Retorna ficha por nome — procura V2 primeiro, fallback V1.

    Wrapper aplicado pra que o cliente continue lendo `atributos`,
    `sub_attributes`, etc. como antes.
    """
    name = (request.GET.get("nome") or "").strip()

    # Procura V2 primeiro
    v2 = CharacterSheetV2.objects.filter(nome_personagem=name).first()
    if v2:
        _wrap_v2_as_legacy(v2)
        data = {
            "id": v2.id,
            "nome_personagem": v2.nome_personagem,
            "atributos": v2.atributos,
            "sub_attributes": v2.sub_attributes,
            "advantages": v2.advantages,
            "disadvantages": v2.disadvantages,
            "skills": v2.skills,
            "equipment_melee": v2.equipment_melee,
            "equipment_ranged": v2.equipment_ranged,
            "equipment_armor": v2.equipment_armor,
            "equipment_misc": v2.equipment_misc,
            "maneuvers_melee": v2.maneuvers_melee,
            "maneuvers_ranged": v2.maneuvers_ranged,
            "maneuvers_defense": v2.maneuvers_defense,
            "info_campanha": v2.info_campanha,
            "pontos_soma": v2.pontos_soma,
            "background": v2.background,
            "aparencia_idade": {"aparencia": v2.aparencia, "idade": v2.idade},
            "money": v2.money,
            "runtime_stats": v2.runtime_stats,
        }
        return JsonResponse(data)

    # Fallback V1
    character = get_object_or_404(CharacterSheet, nome_personagem=name)
    data = {
        field.name: getattr(character, field.name)
        for field in CharacterSheet._meta.fields
    }
    data.pop("photo", None)
    return JsonResponse(data)


@login_required(login_url="gurps:login")
def game_interface_ws(request, campanha_id, slot):
    username = request.user.username
    campanha = get_object_or_404(Campanha, id=campanha_id)

    context = {
        "campanha_id": campanha.id,
        "slot": slot,
        "username": username,
    }
    return render(request, "global/interface_jogo.html", context)


def _broadcast_to_campanha(campanha_id, payload):
    """Manda evento WS pro grupo `chat_<campanha_id>` (todos os clientes conectados)."""
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer

    layer = get_channel_layer()
    if not layer:
        return
    async_to_sync(layer.group_send)(f"chat_{campanha_id}", payload)


@csrf_exempt
@login_required(login_url="gurps:login")
def adjust_character_vitals(request, char_id):
    """GM-only: ajusta HP/FP atuais de uma ficha (V1 ou V2) e broadcasta via WS.

    POST body JSON: {hp_atual?: int, fp_atual?: int}
    Resposta: {ok, char_id, hp_atual, fp_atual, hp_max, fp_max, hp_pct, fp_pct}.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    try:
        body = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid json"}, status=400)

    # Procura V2 primeiro, fallback V1
    char = CharacterSheetV2.objects.filter(pk=char_id).first()
    if char is not None:
        campanha = char.campanha
        is_v2 = True
    else:
        char = CharacterSheet.objects.filter(pk=char_id).first()
        if char is None:
            return JsonResponse({"error": "ficha não existe"}, status=404)
        nome_camp = (char.info_campanha or {}).get("nome_campanha")
        campanha = Campanha.objects.filter(nome=nome_camp).first() if nome_camp else None
        is_v2 = False

    if campanha is None or campanha.dono_id != request.user.id:
        return JsonResponse({"error": "só o GM pode ajustar"}, status=403)

    # Lê max do sub_attributes (V1 nativo) ou wrap (V2)
    if is_v2:
        _wrap_v2_as_legacy(char)
    sub = char.sub_attributes or {}
    hp_max = _safe_int(sub.get("hp"))
    fp_max = _safe_int(sub.get("fp"))

    # Vida vive na CENA ativa (char_runtime). Sem cena → runtime_stats global.
    def _clamp_hp(v):
        return max(-10 * hp_max, min(_safe_int(v, default=hp_max), hp_max))
    def _clamp_fp(v):
        return max(0, min(_safe_int(v, default=fp_max), fp_max))

    _state = campanha.scene_state if isinstance(campanha.scene_state, dict) else {}
    _scenes = _state.get("scenes") or []
    _aid = _state.get("active_scene_id")
    _scene = next((s for s in _scenes if isinstance(s, dict) and s.get("id") == _aid), None)
    if _scene is None and _scenes:
        _scene = _scenes[0]

    if _scene is not None:
        entry = _scene.setdefault("char_runtime", {}).setdefault(str(char.id), {})
        if "hp_atual" in body:
            entry["hp_atual"] = _clamp_hp(body.get("hp_atual"))
        if "fp_atual" in body:
            entry["fp_atual"] = _clamp_fp(body.get("fp_atual"))
        campanha.scene_state = _state
        campanha.save(update_fields=["scene_state"])
        hp_atual = _safe_int(entry.get("hp_atual"), default=hp_max)
        fp_atual = _safe_int(entry.get("fp_atual"), default=fp_max)
    else:
        rs = dict(char.runtime_stats or {})
        if "hp_atual" in body:
            rs["hp_atual"] = _clamp_hp(body.get("hp_atual"))
        if "fp_atual" in body:
            rs["fp_atual"] = _clamp_fp(body.get("fp_atual"))
        char.runtime_stats = rs
        char.save(update_fields=["runtime_stats"])
        hp_atual = _safe_int(rs.get("hp_atual"), default=hp_max)
        fp_atual = _safe_int(rs.get("fp_atual"), default=fp_max)

    hp_pct, hp_is_negative = _hp_pct_and_negative(hp_atual, hp_max)
    fp_pct = f"{100 * fp_atual / fp_max:.1f}" if fp_max > 0 else "0"

    payload = {
        "type": "character_vitals_changed",
        "char_id": char.id,
        "hp_atual": hp_atual,
        "hp_max": hp_max,
        "hp_pct": hp_pct,
        "hp_is_negative": hp_is_negative,
        "fp_atual": fp_atual,
        "fp_max": fp_max,
        "fp_pct": fp_pct,
    }
    _broadcast_to_campanha(campanha.id, payload)
    return JsonResponse({"ok": True, **{k: v for k, v in payload.items() if k != "type"}})


def _serialize_char_for_client(character, viewer_username, viewer_is_gm, campanha=None):
    """Pacote do char enviado via WS/HTTP — mesmo shape que _build_player_mini.

    Detecta V1/V2 e aplica wrapper se for V2.
    """
    if isinstance(character, CharacterSheetV2):
        if campanha is None:
            campanha = character.campanha
        character = _wrap_v2_as_legacy(character)
    owner = (character.info_campanha or {}).get("player_name")
    show_numbers = viewer_is_gm or (owner == viewer_username)
    return _build_player_mini(character, present_ids=None, show_numbers=show_numbers,
                              campanha=campanha)


@login_required(login_url="gurps:login")
def atualizar_pontos_campanha(request, campanha_id):
    """GM edita os pontos da campanha (budget de criação + XP acumulado).

    POST JSON: {pontos_de_ficha, xp_acumulado}. Só o dono (GM) pode.
    Aplica o novo total (pontos_de_ficha + xp_acumulado) como ``available`` de
    TODAS as fichas V2 da campanha e recalcula o ``remaining`` de cada uma
    (via recompute_points no save). Retorna quantas fichas foram atualizadas.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    campanha = get_object_or_404(Campanha, id=campanha_id)
    if campanha.dono_id != request.user.id:
        return JsonResponse({"error": "só o GM pode editar os pontos"}, status=403)
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido"}, status=400)

    pontos = max(0, _safe_int(body.get("pontos_de_ficha"), default=campanha.pontos_de_ficha))
    xp = max(0, _safe_int(body.get("xp_acumulado"), default=campanha.xp_acumulado))
    campanha.pontos_de_ficha = pontos
    campanha.xp_acumulado = xp
    campanha.save(update_fields=["pontos_de_ficha", "xp_acumulado"])

    total = pontos + xp
    updated = 0
    for sheet in CharacterSheetV2.objects.filter(campanha=campanha):
        pts = dict(sheet.points or {})
        pts["available"] = total
        sheet.points = pts
        sheet.save()  # recompute_points recalcula spent/remaining com o novo available
        updated += 1

    return JsonResponse({
        "ok": True,
        "pontos_de_ficha": pontos,
        "xp_acumulado": xp,
        "total": total,
        "updated": updated,
    })


@csrf_exempt
@login_required(login_url="gurps:login")
def save_quick_character(request):
    """GM cria uma ficha rápida (nome + HP + FP + MOVE + asset opcional).

    POST JSON: {campanha_id, nome, hp, fp, move, asset_id?}
    Resposta JSON: {id, nome, ...} (formato compatível com _build_player_mini).
    Broadcast WS: character_created (todos os clientes do grupo recebem).
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    # Aceita JSON (sem imagem) OU multipart/form-data (com upload de imagem no
    # próprio form). Se vier imagem, criamos o asset na hora e linkamos.
    image = None
    if (request.content_type or "").startswith("multipart"):
        data = request.POST
        image = request.FILES.get("image")
    else:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON invalido"}, status=400)

    nome = (data.get("nome") or "").strip()[:30]
    if not nome:
        return JsonResponse({"error": "nome obrigatorio"}, status=400)
    try:
        campanha = Campanha.objects.get(id=int(data.get("campanha_id") or 0))
    except (Campanha.DoesNotExist, ValueError, TypeError):
        return JsonResponse({"error": "campanha invalida"}, status=404)
    if campanha.dono_id != request.user.id:
        return JsonResponse({"error": "so o GM pode criar fichas"}, status=403)

    def _str(v):
        return str(v).strip() if v is not None else "0"

    hp = _str(data.get("hp", "10"))
    fp = _str(data.get("fp", "10"))
    move = _str(data.get("move", "5"))
    asset_id = data.get("asset_id")
    try:
        asset_id_int = int(asset_id) if asset_id else None
    except (TypeError, ValueError):
        asset_id_int = None

    # Quick NPC agora cria CharacterSheetV2 (V1 legado descontinuado).
    # Garante nome único dentro da campanha (V2 tem UniqueConstraint por campanha).
    base = nome
    candidate = nome
    suffix = 1
    while CharacterSheetV2.objects.filter(campanha=campanha, nome_personagem=candidate).exists():
        suffix += 1
        candidate = f"{base} #{suffix}"

    # HP/FP/Move informados pelo GM viram modificadores nas secundárias.
    # Default V2: HP=ST, FP=HT, Move=basic_speed. Pra quick NPC com valores
    # arbitrários, usamos secondary_modifiers pra ajustar.
    hp_int = _safe_int(hp, 10)
    fp_int = _safe_int(fp, 10)
    move_int = _safe_int(move, 5)
    sec_mods = {
        "hp": hp_int - 10,   # delta sobre default ST=10
        "fp": fp_int - 10,   # delta sobre default HT=10
        "basic_move": max(0, move_int - 5),  # delta sobre default 5
    }

    char = CharacterSheetV2.objects.create(
        campanha=campanha,
        owner=request.user,
        nome_personagem=candidate,
        is_quick_npc=True,
        primary_attributes={"st": 10, "dx": 10, "iq": 10, "ht": 10},
        secondary_modifiers=sec_mods,
        runtime_stats={"hp_atual": hp_int, "fp_atual": fp_int},
    )
    # Imagem enviada no próprio form → cria um asset (show=True, slot=2) e linka
    # esse asset (precede o asset_id do dropdown). Mesmas regras do upload normal
    # de asset (ImageField). Assim não é preciso criar o asset separado antes.
    if image is not None:
        try:
            new_asset = CampanhaAssets(
                campanha=campanha, name=candidate[:30], slot=2, show=True,
                description="",
            )
            new_asset.image = image
            new_asset.save()
            asset_id_int = new_asset.id
        except Exception as e:  # noqa: BLE001 — não quebra a ficha se a imagem falhar
            print(f"[save_quick_character] falha ao criar asset da imagem: {e}")

    # Anexa linked_asset_id como atributo de runtime (não é campo do model)
    if asset_id_int is not None:
        rs = char.runtime_stats or {}
        rs["linked_asset_id"] = asset_id_int
        char.runtime_stats = rs
        char.save(update_fields=["runtime_stats"])

    # Wrapper compat pra _build_player_mini ler
    _wrap_v2_as_legacy(char)
    # Re-popula info_campanha com linked_asset_id pro avatar resolver corretamente
    char.info_campanha["linked_asset_id"] = asset_id_int

    char_data = _build_player_mini(char, present_ids=None, show_numbers=True, campanha=campanha)

    _broadcast_to_campanha(
        campanha.id,
        {"type": "character_created", "char": char_data},
    )
    return JsonResponse({"ok": True, "char": char_data})


@csrf_exempt
@login_required(login_url="gurps:login")
def delete_quick_character(request, char_id):
    """GM deleta permanentemente uma ficha + limpa de scene_state de toda campanha.

    Procura primeiro em CharacterSheetV2 (novo), fallback em V1.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    char = CharacterSheetV2.objects.filter(id=char_id).first()
    if char:
        if not char.is_quick_npc:
            return JsonResponse(
                {"error": "essa ficha não foi criada via quick-create; delete pela tela de fichas"},
                status=403,
            )
        campanha = char.campanha
    else:
        # Fallback V1
        try:
            char = CharacterSheet.objects.get(id=char_id)
        except CharacterSheet.DoesNotExist:
            return JsonResponse({"error": "ficha nao existe"}, status=404)
        info = char.info_campanha or {}
        if not info.get("is_quick_npc"):
            return JsonResponse(
                {"error": "essa ficha não foi criada via quick-create; delete pela tela de fichas"},
                status=403,
            )
        nome_campanha = info.get("nome_campanha")
        campanha = Campanha.objects.filter(nome=nome_campanha).first() if nome_campanha else None

    if not campanha or campanha.dono_id != request.user.id:
        return JsonResponse({"error": "so o GM da campanha pode deletar"}, status=403)

    # Limpa de qualquer scene_state que referencie esse char.
    target_id = char.id
    if isinstance(campanha.scene_state, dict):
        scene_state = campanha.scene_state
        changed = False
        for scene in scene_state.get("scenes", []) or []:
            ids = scene.get("character_ids") or []
            if target_id in ids:
                scene["character_ids"] = [x for x in ids if x != target_id]
                changed = True
            if scene.get("current_turn_id") == target_id:
                scene["current_turn_id"] = (scene["character_ids"] or [None])[0]
                changed = True
        if changed:
            campanha.scene_state = scene_state
            campanha.save(update_fields=["scene_state"])

    char.delete()

    _broadcast_to_campanha(
        campanha.id,
        {
            "type": "character_deleted",
            "char_id": target_id,
            "scene_state": campanha.scene_state or {},
        },
    )
    return JsonResponse({"ok": True, "char_id": target_id})


@login_required(login_url="gurps:login")
def journal(request, campanha_id):
    username = request.user.username
    campanha = get_object_or_404(Campanha, id=campanha_id)
    # Mix de V2 + V1 (V1 só se não tem V2 do mesmo owner)
    personagens_journal = _get_all_sheets_for_campanha(campanha)
    assets_player = CampanhaAssets.objects.filter(
        campanha=campanha, slot__in=[1, 2], show=True
    ).order_by("-id")
    assets_gm = CampanhaAssets.objects.filter(
        campanha=campanha,
    ).order_by("-id")
    print(f"\nPERSONAGENS JOURNAL: {personagens_journal}\n")

    context = {
        "personagens_journal": personagens_journal,
        "campanha": campanha,
        "username": username,
        "assets_player": assets_player,
        "assets_gm": assets_gm,
    }
    return render(request, "global/journal.html", context)


@login_required(login_url="gurps:login")
def journal_data(request, campanha_id):
    """JSON do journal pra recarregar sem refresh: personagens + assets atuais.

    GM vê todos os assets slot 1/2 (inclusive show=False); player só show=True.
    Personagens vêm com avatar_url resolvido (foto OU asset linkado).
    """
    campanha = get_object_or_404(Campanha, id=campanha_id)
    is_gm = (campanha.dono_id == request.user.id)
    chars = _get_all_sheets_for_campanha(campanha)
    personagens = [{
        "id": p.id,
        "nome": p.nome_personagem,
        "background": (getattr(p, "background", "") or "")[:400],
        "avatar_url": _resolve_avatar_url(p),
    } for p in chars]
    aq = CampanhaAssets.objects.filter(campanha=campanha, slot__in=[1, 2])
    if not is_gm:
        aq = aq.filter(show=True)
    assets = [{
        "id": a.id,
        "name": a.name,
        "description": a.description or "",
        "image_url": (a.image.url if a.image else None),
        "show": a.show,
    } for a in aq.order_by("-id")]
    return JsonResponse({"ok": True, "is_gm": is_gm,
                         "personagens": personagens, "assets": assets})
