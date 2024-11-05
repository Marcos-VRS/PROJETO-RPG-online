from django.shortcuts import render, redirect
from gurps.models import FichaPersonagem, Campanha
from django.contrib.auth.decorators import login_required
from gurps.forms import FichaPersonagemForm


# View da pagina inicial
@login_required(login_url="gurps:login")
def index(request):
    username = request.user.username
    print(f"\n  O USUÁRIO [{username}] ACESSOU O INDEX\n")

    return render(request, "gurps/index.html", {"username": username})


@login_required(login_url="gurps:login")
def nova_campanha(): ...


@login_required(login_url="gurps:login")
def carregar_campanha(): ...


@login_required(login_url="gurps:login")
def carregar_ficha_view(): ...


@login_required(login_url="gurps:login")
def criar_ficha_view(request, campanha_id):
    campanha = Campanha.objects.get(id=campanha_id)

    if request.method == "POST":
        form = FichaPersonagemForm(request.POST)
        if form.is_valid():
            ficha = form.save(commit=False)
            ficha.nome_jogador = request.user
            ficha.campanha = campanha
            ficha.save()
            return redirect("some_view_to_redirect_after_creation")
    else:
        form = FichaPersonagemForm()

    return render(
        request, "caminho/para/criar_ficha.html", {"form": form, "campanha": campanha}
    )
