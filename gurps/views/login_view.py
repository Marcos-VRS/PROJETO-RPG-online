from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


# view de login
def login(request):
    print("Essa é a login")
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("index")
        else:
            messages.error(request, "Usuário ou senha inválidos.")

    return render(request, "gurps/login.html")


# View de logout
def logout_view(request):
    print("Essa é a logout")

    logout(request)
    return redirect("login")  # Redirecionar para a página de login após logout
