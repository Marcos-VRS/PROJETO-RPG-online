from django.shortcuts import render


# View da pagina inicial
def index(request):
    return render(request, "gurps/index.html")
