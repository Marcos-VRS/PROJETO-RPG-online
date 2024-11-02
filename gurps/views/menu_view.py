from django.shortcuts import render


# View da pagina inicial
def index(request):
    print("Página acessada : Index")

    return render(request, "gurps/index.html")
