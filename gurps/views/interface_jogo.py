import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from gurps.models import Campanha, CampanhaAssets, Message, CharacterSheet
from django.contrib.auth.decorators import login_required
from django.contrib import auth
import random


@login_required(login_url="gurps:login")
def game_interface(request, campanha_id, slot):
    username = request.user.username
    campanha = get_object_or_404(Campanha, id=campanha_id)
    pagina_inicial = get_object_or_404(CampanhaAssets, campanha=campanha, slot=slot)
    messages = Message.objects.filter(campanha=campanha).order_by("timestamp")
    assets = CampanhaAssets.objects.filter(
        campanha=campanha, slot__in=[1, 2], show=True
    ).order_by("-id")

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
