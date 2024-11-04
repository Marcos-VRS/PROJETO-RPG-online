from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model

from ..forms import RegisterUserForm  # Importe o formulário
from django.urls import reverse


def login_view(request):
    print(f"\n  O USUÁRIO CLICOU EM LOGIN \n")
    form = AuthenticationForm(request)

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            auth.login(request, user)
            login_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            messages.success(request, "Logado com sucesso")
            print(f"\n  O USUÁRIO [{user}] LOGOU - {login_time}\n")
            return redirect("gurps:index")

        messages.error(request, "Login inválido")

    return render(request, "gurps/login.html", {"form": form})


@login_required(login_url="gurps:login")
def logout_view(request):
    username = request.user.username
    print(f"\n  O USUÁRIO [{username}] CLICOU EM LOGOUT\n")
    auth.logout(request)
    return redirect("gurps:login")


def register_view(request):

    User = get_user_model()

    print("\n O USUÁRIO CLICOU EM REGISTRA-SE\n")

    if request.method == "POST":
        form = RegisterUserForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(
                form.cleaned_data["password"]
            )  # Use set_password em vez de make_password
            user.save()

            messages.success(request, "User registered successfully!")
            return redirect("gurps:login")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = RegisterUserForm()

    return render(request, "gurps/register.html", {"form": form})
