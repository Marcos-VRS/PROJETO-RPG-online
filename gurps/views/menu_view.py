from django.shortcuts import render
from django.contrib.auth.decorators import login_required


# View da pagina inicial
@login_required(login_url="gurps:login")
def index(request):
    username = request.user.username
    print(f"\n  O USUÁRIO [{username}] ACESSOU O INDEX\n")

    return render(request, "gurps/index.html", {"username": username})


def nova_campanha(): ...


def carregar_campanha(): ...
