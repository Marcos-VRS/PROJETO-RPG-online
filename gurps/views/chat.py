from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from gurps.models import Grupo_Chat


@login_required(login_url="gurps:login")
def chat_view(request):
    grupo_chat = get_object_or_404(Grupo_Chat, group_name="Chat publico teste")
    mensagens_chat = grupo_chat.mensagens_chat.all()[:30]
    return render(request, "global/chat.html", {"mensagens_chat": mensagens_chat})
