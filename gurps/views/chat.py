from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from gurps.models import Grupo_Chat
from gurps.forms import *


@login_required(login_url="gurps:login")
def chat_view(request):
    grupo_chat = get_object_or_404(Grupo_Chat, group_name="chat-publico")
    mensagens_chat = grupo_chat.mensagens_chat.all()[:30]

    if request.method == "POST":
        form = ChatmessageCreateForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.grupo = grupo_chat  # Atribua o grupo à mensagem
            message.autor = request.user  # Atribua o autor à mensagem
            message.save()
            return redirect(
                "gurps:chat_view"
            )  # Redireciona para a mesma página após salvar a mensagem
        else:
            # Lidar com o caso em que o formulário não é válido
            print(form.errors)  # Mostra erros no console de desenvolvimento
            return render(
                request,
                "global/chat.html",
                {"mensagens_chat": mensagens_chat, "form": form},
            )

    # Se o método não for POST, só renderize as mensagens existentes
    form = ChatmessageCreateForm()
    return render(
        request, "global/chat.html", {"mensagens_chat": mensagens_chat, "form": form}
    )
