import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from gurps.models import Campanha, CampanhaAssets, Message
from django.contrib.auth.decorators import login_required
from django.contrib import auth
import random


@login_required(login_url="gurps:login")
def game_interface(request, campanha_id, slot):
    campanha = get_object_or_404(Campanha, id=campanha_id)
    pagina_inicial = get_object_or_404(CampanhaAssets, campanha=campanha, slot=slot)
    messages = Message.objects.filter(campanha=campanha).order_by("timestamp")

    context = {
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


@login_required(login_url="gurps:login")
def roll_d6(quantidade: int, incremento: int) -> int:
    """Rola uma quantidade de dados de 6 lados e aplica um incremento."""
    resultado = sum(random.randint(1, 6) for _ in range(quantidade)) + incremento
    return resultado


def verify_roll(nh: int, roll: int) -> str:
    """Verifica se o resultado de um teste de habilidade foi um sucesso ou falha."""
    result = roll - nh

    if roll == 18:
        message = "ERRO CRÍTICO"
        return message

    elif roll == 3:
        message = "SUCESSO DECISIVO"
        return message

    elif roll == 4:
        message = "SUCESSO"
        return message

    elif roll == 5 and nh >= 15:
        message = "SUCESSO"
        return message

    elif roll == 6 and nh >= 16:
        message = "SUCESSO"
        return message

    elif roll == 17:
        message = "Falha"
        return message

    elif roll >= (nh + 10):
        message = "ERRO CRÍTICO"
        return message

    elif result >= 0:
        message = "Acerto"
        return message

    elif result < 0:
        message = "Falha"
        return message


@login_required(login_url="gurps:login")
def roll_test_skill(nh_skill: int):
    roll = roll_d6(3, 0)
    nh = nh_skill
    message = verify_roll(nh, roll)
    return message
