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
    campanha = get_object_or_404(Campanha, id=campanha_id)
    pagina_inicial = get_object_or_404(CampanhaAssets, campanha=campanha, slot=slot)
    messages = Message.objects.filter(campanha=campanha).order_by("timestamp")
    personagem = CharacterSheet.objects.filter(
        info_campanha__nome_campanha=campanha.nome,
        info_campanha__player_name=request.user.username,
    ).first()

    context = {
        "personagem": personagem,
        "campanha": campanha,
        "pagina_inicial": pagina_inicial,
        "messages": messages,
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
    request, atributo: str, nh_attribute: int, bonus: int, redutor: int
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
        }
    )


@login_required(login_url="gurps:login")
def roll_test_skill(nh_skill: int):
    roll = roll_d6(3, 0)
    nh = nh_skill
    message = verify_roll(nh, roll)
    print(f"\nNH: {nh}, ROLL: {roll}, MESSAGE: {message}\n")
    return message
