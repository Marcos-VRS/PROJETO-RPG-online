from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.contrib.auth.hashers import make_password
from ..forms import RegisterUserForm  # Importe o formulário
from django.urls import reverse


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

    return render(request, "gurps/login.html", {"form": form})


@login_required(login_url="gurps:login")
def logout_view(request):
    auth.logout(request)
    return redirect("gurps:login")


def register_view(request):
    print("\n aqui está o REGISTER \n")
    if request.method == "POST":
        print("passou pelo IF")
        form = RegisterUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.password = make_password(
                form.cleaned_data["password"]
            )  # Hashear a senha
            user.save()
            messages.success(request, "User registered successfully!")

            return redirect("gurps:login")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        print("aqui está o else externo")
        form = RegisterUserForm()

    return render(request, "gurps/register.html", {"form": form})
