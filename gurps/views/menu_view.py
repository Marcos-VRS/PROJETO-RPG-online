from django.shortcuts import render, redirect, get_object_or_404
from gurps.models import CharacterSheet, Campanha
from django.contrib.auth.decorators import login_required
from gurps.forms import CharacterSheetForm, CampanhaForm
from django.contrib import messages
from django.http import JsonResponse


# View da pagina inicial
@login_required(login_url="gurps:login")
def index(request):
    username = request.user.username
    print(f"\n  O USUÁRIO [{username}] ACESSOU O INDEX\n")

    return render(request, "gurps/index.html", {"username": username})


# Views da parte de Nova Campanha
@login_required(login_url="gurps:login")
def nova_campanha(request):
    username = request.user.username
    print(f"\n  O USUÁRIO [{username}] CLICOU EM NOVA CAMPANHA\n")

    return render(request, "global/partials/_nova_campanha_index.html")


@login_required(login_url="gurps:login")
def criar_campanha(request):
    username = request.user.username
    print(f"\n  O USUÁRIO [{username}] CLICOU EM GAME MASTER\n")

    if request.method == "POST":
        form = CampanhaForm(request.POST, request.FILES)
        nome_campanha = request.POST.get("nome")
        if form.is_valid():
            campanha = form.save(commit=False)
            campanha.dono = request.user  # define o usuário logado como dono
            if "imagem" in request.FILES:
                campanha.imagem = request.FILES["imagem"]  # Atribui o arquivo de imagem

            campanha.save()
            messages.success(request, "Campanha criada com sucesso!")
            print(
                f"\n  O USUÁRIO [{username}] CRIOU UMA NOVA CAMPANHA COM O NOME [{nome_campanha}]\n"
            )
            return redirect("gurps:index")  # Altere para a URL desejada após a criação
    else:
        form = CampanhaForm()

    return render(request, "global/criar_campanha.html", {"form": form})


def lista_campanhas(request):
    campanhas = Campanha.objects.all()  # Recupera todas as campanhas
    return render(
        request, "global/lista_campanhas_nova_campanha.html", {"campanhas": campanhas}
    )


@login_required(login_url="gurps:login")
def save_character_sheet(request):
    username = request.user.username
    if request.method == "POST":
        form = CharacterSheetForm(
            request.POST, request.FILES
        )  # Inclui arquivos para o campo `photo`

        if form.is_valid():
            # Salva os dados no banco de dados
            character_sheet = form.save()
            print(f"O usuário {username} Salvou a ficha ")
            # Resposta de sucesso
            return JsonResponse(
                {
                    "success": True,
                    "message": "Ficha salva com sucesso!",
                    "character_id": character_sheet.id,
                },
                status=200,
            )
        else:
            # Resposta de erro com detalhes
            print(f"\nAqui está o erro\n ")
            return JsonResponse(
                {
                    "success": False,
                    "message": "Erro ao salvar a ficha.",
                    "errors": form.errors,
                },
                status=400,
            )
    else:
        print("\naqui é o else\n")

        # Renderiza o formulário para criar/editar uma ficha
        form = CharacterSheetForm()

    return render(
        request,
        "global/criar_ficha.html",
        {
            "form": form,
            "username": username,
        },
    )


@login_required(login_url="gurps:login")
def carregar_campanha_index(request):
    username = request.user.username
    print(f"\n  O USUÁRIO [{username}] CLICOU EM CARREGAR CAMPANHA\n")
    return render(request, "global/partials/_carregar_campanha_index.html")


@login_required(login_url="gurps:login")
def criar_ficha_campanha(request, id):
    username = request.user.username
    campanha = get_object_or_404(Campanha, id=id)  # Busca a campanha pelo ID
    print(
        f"\n  O USUÁRIO [{username}] ESCOLHEU A CAMPANHA [{campanha.nome}] do GM [{campanha.dono}]\n"
    )
    return render(
        request, "global/criar_ficha.html", {"campanha": campanha, "username": username}
    )


@login_required(login_url="gurps:login")
def fichas(request):
    username = request.user.username
    print(f"\n  O USUÁRIO [{username}] CLICOU EM FICHAS\n")
    return render(request, "global/partials/_fichas_index.html")


@login_required(login_url="gurps:login")
def opcoes(request):
    username = request.user.username
    print(f"\n  O USUÁRIO [{username}] CLICOU EM OPÇÕES\n")
    return render(request, "global/partials/_opcoes_index.html")


@login_required(login_url="gurps:login")
def carregar_ficha_view(): ...
