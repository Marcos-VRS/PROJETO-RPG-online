import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from gurps.models import Campanha, CampanhaAssets, Message
from django.contrib.auth.decorators import login_required
from django.contrib import auth


@login_required(login_url="gurps:login")
def show_mapas(request, campanha_id, campanha_assets_id):
    campanha = get_object_or_404(Campanha, id=campanha_id)
    pagina_inicial = get_object_or_404(
        CampanhaAssets, id=campanha_assets_id, campanha=campanha
    )
    messages = Message.objects.filter(campanha=campanha).order_by("timestamp")

    context = {
        "campanha": campanha,
        "pagina_inicial": pagina_inicial,
        "messages": messages,
    }
    return render(request, "global/interface_jogo.html", context)


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
def leave_game(request):
    username = request.user.username
    print(f"\n  O USUÁRIO [{username}] CLICOU EM LEAVE GAME\n")
    return redirect("gurps:index")
