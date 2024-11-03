from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from datetime import datetime


def login_view(request):
    form = AuthenticationForm(request)

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            auth.login(request, user)
            login_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            messages.success(request, "Logado com sucesso")
            print(f"Usuário: {user} - Data e hora do login: {login_time}")
            return redirect("gurps:index")

        messages.error(request, "Login inválido")

    return render(request, "gurps:login", {"form": form})


@login_required(login_url="gurps:login")
def logout_view(request):
    auth.logout(request)
    return redirect("gurps:login")
