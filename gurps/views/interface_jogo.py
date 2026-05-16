import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from gurps.models import Campanha, CampanhaAssets, Message, CharacterSheet
from django.contrib.auth.decorators import login_required
from django.contrib import auth
import random


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


def _resolve_avatar_url(character):
    """Avatar: photo do char se houver, senão image do asset linkado (quick char), senão None."""
    if character.photo:
        try:
            return character.photo.url
        except Exception:
            pass
    info = character.info_campanha or {}
    linked = info.get("linked_asset_id")
    if linked:
        try:
            asset = CampanhaAssets.objects.get(id=int(linked))
            if asset.image:
                return asset.image.url
        except (CampanhaAssets.DoesNotExist, ValueError, TypeError):
            pass
    return None


def _build_player_mini(character, present_ids=None, show_numbers=False):
    """Empacota a ficha num dicionário leve pra exibição da barra de players.

    ``show_numbers`` controla privacidade: True → mostra ``HP X/Y`` e ``FP X/Y``
    em texto sobre a barra; False → só a barra colorida sem os valores. GM
    sempre tem show_numbers=True; players têm True só na própria ficha.
    """
    sub = character.sub_attributes or {}
    runtime = character.runtime_stats or {}
    hp_max = _safe_int(sub.get("hp"))
    fp_max = _safe_int(sub.get("fp"))
    hp_atual = _safe_int(runtime.get("hp_atual"), default=hp_max)
    fp_atual = _safe_int(runtime.get("fp_atual"), default=fp_max)
    speed = _safe_float(sub.get("speed"))
    nome = character.nome_personagem or "?"
    initials = ("".join(w[0] for w in nome.split()[:2]) or "?").upper()
    hp_pct = f"{100 * hp_atual / hp_max:.1f}" if hp_max > 0 else "0"
    fp_pct = f"{100 * fp_atual / fp_max:.1f}" if fp_max > 0 else "0"
    is_present = present_ids is None or character.id in present_ids
    info = character.info_campanha or {}
    return {
        "id": character.id,
        "nome": nome,
        "initials": initials,
        "avatar_url": _resolve_avatar_url(character),
        "hp_atual": hp_atual,
        "hp_max": hp_max,
        "hp_pct": hp_pct,
        "fp_atual": fp_atual,
        "fp_max": fp_max,
        "fp_pct": fp_pct,
        "speed": speed,
        "is_present": is_present,
        "show_numbers": show_numbers,
        "is_quick_npc": bool(info.get("is_quick_npc")),
    }


@login_required(login_url="gurps:login")
def game_interface(request, campanha_id, slot):
    username = request.user.username
    campanha = get_object_or_404(Campanha, id=campanha_id)
    pagina_inicial = get_object_or_404(CampanhaAssets, campanha=campanha, slot=slot)
    messages = Message.objects.filter(campanha=campanha).order_by("timestamp")
    assets = CampanhaAssets.objects.filter(
        campanha=campanha, slot__in=[1, 2], show=True
    ).order_by("-id")
    # Lista completa dos assets pro GM linkar fichas rápidas a (visíveis ou não).
    all_assets_for_gm = list(
        CampanhaAssets.objects.filter(campanha=campanha).order_by("-id").values("id", "name")
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

    personagem = CharacterSheet.objects.filter(
        info_campanha__nome_campanha=campanha.nome,
        info_campanha__player_name=request.user.username,
    ).first()
    personagens_gm = CharacterSheet.objects.filter(
        info_campanha__nome_campanha=campanha.nome,
        info_campanha__player_name=request.user.username,
    ).order_by("-id")

    personagens_journal = CharacterSheet.objects.filter(
        info_campanha__nome_campanha=campanha.nome
    ).order_by("-id")

    sheets = CharacterSheet.objects.all().filter(
        info_campanha__nome_campanha=campanha.nome,
        info_campanha__player_name=username,
    )
    if sheets.exists():
        first_id_sheet = sheets.first()
        sheet_list = sheets.exclude(id=first_id_sheet.id).order_by("id")
    else:
        first_id_sheet = None
        sheet_list = []
    print(f"\nSHEETS: {sheets}\n")
    print(f"\nFIRST ID SHEET: {first_id_sheet}\n")
    print(f"\nSHEET LIST: {sheet_list}\n")
    # Estado multi-cena (controlado pelo GM, sincronizado via WS).
    scene_state = _migrate_scene_state(campanha.scene_state)
    scenes = scene_state.get("scenes") or []
    active_scene_id = scene_state.get("active_scene_id")
    active_scene = next((s for s in scenes if s.get("id") == active_scene_id), None)
    if active_scene is None and scenes:
        active_scene = scenes[0]
        scene_state["active_scene_id"] = active_scene["id"]

    # Personagens "em cena" e ordem vêm da cena ativa. Se não há cena ainda,
    # todos são considerados presentes (estado inicial = nenhuma cena criada).
    if active_scene:
        order_ids = active_scene.get("character_ids") or []
        present_ids = set(order_ids)
    else:
        order_ids = []
        present_ids = None

    from django.conf import settings as dj_settings

    is_gm = (campanha.dono_id is not None) and (campanha.dono_id == request.user.id)

    # Minis de todos os personagens da campanha (privacidade aplicada).
    players_minis = []
    for p in personagens_journal:
        owner = (p.info_campanha or {}).get("player_name")
        show_numbers = is_gm or (owner == username)
        players_minis.append(_build_player_mini(p, present_ids, show_numbers))

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
        "personagens_journal": personagens_journal,
        "sheet_list": sheet_list,
        "players_minis": players_minis,
        "is_gm": is_gm,
        "scene_state": scene_state,
        "all_characters_data": [
            {"id": p["id"], "nome": p["nome"], "speed": p["speed"], "is_quick_npc": p["is_quick_npc"]} for p in players_minis
        ],
        "all_assets_for_gm": all_assets_for_gm,
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
    name = request.GET.get("nome").strip()  # Obtém o nome do personagem da query string
    character = get_object_or_404(CharacterSheet, nome_personagem=name)  # Busca no BD

    print(f"\nCHARACTER NAME: {name}\n")  # Debug para verificar no terminal

    # Cria o dicionário dinamicamente, pegando todos os campos do modelo
    data = {
        field.name: getattr(character, field.name)
        for field in CharacterSheet._meta.fields
    }

    # Remove o campo 'photo' se ele existir
    data.pop("photo", None)

    print(f"\nCHARACTER SHEET: {data}\n")

    return JsonResponse(data)  # Retorna os dados como JSON


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


def _serialize_char_for_client(character, viewer_username, viewer_is_gm):
    """Pacote do char enviado via WS/HTTP — mesmo shape que _build_player_mini."""
    owner = (character.info_campanha or {}).get("player_name")
    show_numbers = viewer_is_gm or (owner == viewer_username)
    return _build_player_mini(character, present_ids=None, show_numbers=show_numbers)


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

    # Evita colisão do unique=True em nome_personagem com sufixo numérico.
    base = nome
    candidate = nome
    suffix = 1
    while CharacterSheet.objects.filter(nome_personagem=candidate).exists():
        suffix += 1
        candidate = f"{base} #{suffix}"

    char = CharacterSheet.objects.create(
        nome_personagem=candidate,
        info_campanha={
            "player_name": request.user.username,
            "nome_campanha": campanha.nome,
            "nome_gm": campanha.dono.username if campanha.dono else "",
            "is_quick_npc": True,
            "linked_asset_id": asset_id_int,
        },
        sub_attributes={
            "hp": hp,
            "fp": fp,
            "move": move,
            "speed": "0",
        },
    )

    # Empacota com show_numbers=True (o GM que criou vê tudo); cada cliente
    # decide na hora de renderizar se mostra os números ou só barras (via
    # `show_numbers` recomputado client-side baseado em viewer.username).
    char_data = _build_player_mini(char, present_ids=None, show_numbers=True)

    _broadcast_to_campanha(
        campanha.id,
        {"type": "character_created", "char": char_data},
    )
    return JsonResponse({"ok": True, "char": char_data})


@csrf_exempt
@login_required(login_url="gurps:login")
def delete_quick_character(request, char_id):
    """GM deleta permanentemente uma ficha + limpa de scene_state de toda campanha."""
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    try:
        char = CharacterSheet.objects.get(id=char_id)
    except CharacterSheet.DoesNotExist:
        return JsonResponse({"error": "ficha nao existe"}, status=404)

    info = char.info_campanha or {}
    # Só fichas criadas via "+ Nova ficha rápida" podem ser deletadas aqui.
    # Fichas importadas da produção GCP (sem `is_quick_npc`) ficam protegidas.
    if not info.get("is_quick_npc"):
        return JsonResponse(
            {"error": "essa ficha não foi criada via quick-create; delete pela tela de fichas"},
            status=403,
        )

    # Verifica que o usuário é GM da campanha desta ficha.
    nome_campanha = info.get("nome_campanha")
    campanha = None
    if nome_campanha:
        campanha = Campanha.objects.filter(nome=nome_campanha).first()
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
    personagens_journal = CharacterSheet.objects.filter(
        info_campanha__nome_campanha=campanha.nome
    ).order_by("-id")
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
