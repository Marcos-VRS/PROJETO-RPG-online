from django.shortcuts import render
from django.contrib.auth.decorators import login_required


# View da pagina inicial
@login_required(login_url="gurps:login")
def index(request):
    print("Página acessada : Index")

    return render(request, "gurps/index.html")
