from django.shortcuts import render, get_object_or_404, redirect
from gurps.models import Campanha, Message


def chat_view(request, campanha_id):
    # Obter a campanha específica
    campanha = get_object_or_404(Campanha, id=campanha_id)
    # Filtrar as mensagens associadas à campanha
    messages = Message.objects.filter(campanha=campanha).order_by("timestamp")

    if request.method == "POST":
        # Verificar se o formulário foi enviado
        content = request.POST.get("content")  # Obter o conteúdo da mensagem
        if content:  # Certificar-se de que não está vazio
            Message.objects.create(
                user=request.user,  # Usuário logado
                campanha=campanha,  # Campanha atual
                content=content,
            )
            return redirect(
                "gurps:chat", campanha_id=campanha_id
            )  # Recarregar a página

    context = {
        "campanha": campanha,
        "messages": messages,  # Passar as mensagens associadas
    }

    return render(request, "global/chat.html", context)
