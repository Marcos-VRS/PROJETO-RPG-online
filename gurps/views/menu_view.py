from django.shortcuts import render, redirect, get_object_or_404
from gurps.models import CharacterSheet, Campanha, CampanhaAssets
from django.contrib.auth.decorators import login_required
from gurps.forms import CharacterSheetForm, CampanhaForm
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse


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
        if form.is_valid():
            campanha = form.save(commit=False)
            campanha.dono = request.user
            campanha.save()

            # Criar um asset automaticamente para a campanha
            CampanhaAssets.objects.create(
                campanha=campanha,
                name=campanha.nome,
                description=campanha.descricao,
                image=campanha.imagem,
            )

            messages.success(request, "Campanha criada com sucesso!")
            print(
                f"\n  O USUÁRIO [{username}] CRIOU UMA NOVA CAMPANHA COM O NOME [{campanha.nome}]\n"
            )

            # Redirecionar para a URL da interface do jogo, passando o ID da campanha e slot=1
            return redirect(reverse("gurps:game_interface", args=[campanha.id, 1]))

    else:
        form = CampanhaForm()

    return render(request, "global/criar_campanha.html", {"form": form})


@login_required(login_url="gurps:login")
def lista_campanhas(request):
    campanhas = Campanha.objects.all().order_by("-id")  # Recupera todas as campanhas
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

    campanhas = Campanha.objects.filter(
        dono=request.user
    )  # Filtra as campanhas do usuário
    print(f"\n  O USUÁRIO [{username}] CARREGOU AS CAMPANHAS {campanhas}\n")

    return render(request, "global/partials/_carregar_campanha_index.html")


@login_required(login_url="gurps:login")
def carregar_campanha_gm(request):
    username = request.user.username
    campanhas = Campanha.objects.filter(dono__username=username).order_by("-id")
    asset_id = "1"  # Variável fixa ou pode ser dinâmica conforme necessário
    context = {"campanhas": campanhas, "asset_id": asset_id}
    print(f"\n  O USUÁRIO [{username}] CARREGOU AS CAMPANHAS {campanhas}\n")
    return render(
        request,
        "global/partials/_lista_carregar_campanha_gm.html",
        context,
    )


@login_required(login_url="gurps:login")
def carregar_campanha_player(request):
    username = request.user.username

    personagens = (
        CharacterSheet.objects.filter(info_campanha__player_name=username)
        .distinct()
        .order_by("-id")
    )

    # Criar um dicionário para mapear nome da campanha para id
    campanhas_dict = {campanha.nome: campanha.id for campanha in Campanha.objects.all()}

    # Adicionar o ID da campanha dentro de cada personagem no contexto
    for personagem in personagens:
        nome_campanha = personagem.info_campanha.get("nome_campanha")
        personagem.campanha_id = campanhas_dict.get(
            nome_campanha, None
        )  # Adicionando dinamicamente o ID da campanha

    asset_id = "1"  # Variável fixa ou pode ser dinâmica conforme necessário

    context = {
        "personagens": personagens,
        "asset_id": asset_id,
    }
    return render(
        request,
        "global/partials/_lista_carregar_campanha_player.html",
        context,
    )


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
