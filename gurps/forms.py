from django import forms
from .models import RegisterUser, FichaPersonagem
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _


class RegisterUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    confirm_password = forms.CharField(
        widget=forms.PasswordInput, label="Confirm Password"
    )

    class Meta:
        model = RegisterUser
        fields = ["username", "email", "password", "confirm_password"]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            self.add_error("confirm_password", "Passwords do not match.")


class LoginForm(forms.Form):
    username = forms.CharField(label=_("Username"), max_length=150)
    password = forms.CharField(widget=forms.PasswordInput, label=_("Password"))

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        if username and password:
            user = authenticate(username=username, password=password)
            if user is None:
                raise forms.ValidationError(_("Invalid username or password."))
        return cleaned_data


class FichaPersonagemForm(forms.ModelForm):
    class Meta:
        model = FichaPersonagem
        # Exclui 'nome_jogador' e 'campanha' para que eles sejam preenchidos automaticamente
        exclude = ["nome_jogador", "campanha"]
        widgets = {
            "nome_personagem": forms.TextInput(attrs={"class": "form-control"}),
            "idade": forms.NumberInput(attrs={"class": "form-control"}),
            "aparencia": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "altura": forms.NumberInput(attrs={"class": "form-control"}),
            "peso": forms.NumberInput(attrs={"class": "form-control"}),
            "total_de_pontos": forms.NumberInput(attrs={"class": "form-control"}),
            "pontos_de_experiencia_guardados": forms.NumberInput(
                attrs={"class": "form-control"}
            ),
            "pontos_de_vantagens": forms.NumberInput(attrs={"class": "form-control"}),
            "pontos_de_desvantagens": forms.NumberInput(
                attrs={"class": "form-control"}
            ),
            "pontos_de_pericias": forms.NumberInput(attrs={"class": "form-control"}),
            "pontos_de_atributos": forms.NumberInput(attrs={"class": "form-control"}),
            "st": forms.NumberInput(attrs={"class": "form-control"}),
            "xpst": forms.NumberInput(attrs={"class": "form-control"}),
            "dx": forms.NumberInput(attrs={"class": "form-control"}),
            "xpdx": forms.NumberInput(attrs={"class": "form-control"}),
            "iq": forms.NumberInput(attrs={"class": "form-control"}),
            "xpiq": forms.NumberInput(attrs={"class": "form-control"}),
            "ht": forms.NumberInput(attrs={"class": "form-control"}),
            "xpht": forms.NumberInput(attrs={"class": "form-control"}),
            "damage": forms.TextInput(attrs={"class": "form-control"}),
            "basic_lift": forms.NumberInput(attrs={"class": "form-control"}),
            "hp": forms.NumberInput(attrs={"class": "form-control"}),
            "will": forms.NumberInput(attrs={"class": "form-control"}),
            "perception": forms.NumberInput(attrs={"class": "form-control"}),
            "fp": forms.NumberInput(attrs={"class": "form-control"}),
            "basic_speed": forms.NumberInput(attrs={"class": "form-control"}),
            "basic_move": forms.NumberInput(attrs={"class": "form-control"}),
            "advantages": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "disadvantages": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "skills": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "equipments": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
