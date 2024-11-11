from django import forms
from .models import RegisterUser, FichaPersonagem, Campanha
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


class CampanhaForm(forms.ModelForm):
    class Meta:
        model = Campanha
        fields = [
            "nome",
            "xp_inicial",
            "pontos_de_desvantagens",
            "tl",
            "descricao",
            "regras",
        ]
        widgets = {
            "descricao": forms.Textarea(attrs={"rows": 4, "cols": 40}),
            "regras": forms.Textarea(attrs={"rows": 4, "cols": 40}),
        }


class FichaPersonagemForm(forms.ModelForm):
    class Meta:
        model = FichaPersonagem
        fields = [
            "nome_jogador",
            "campanha",
            "nome_personagem",
            "idade",
            "aparencia",
            "altura",
            "peso",
            "tl",
            "total_de_pontos",
            "pontos_de_experiencia_guardados",
            "pontos_de_vantagens",
            "pontos_de_desvantagens",
            "pontos_de_pericias",
            "pontos_de_atributos",
            "attributes",
            "subattributes",
            "advantages",
            "disadvantages",
            "skills",
            "equipments",
        ]
        widgets = {
            # Torna os campos 'nome_jogador' e 'campanha' somente leitura
            "nome_jogador": forms.TextInput(attrs={"readonly": "readonly"}),
            "campanha": forms.TextInput(attrs={"readonly": "readonly"}),
            # Outros widgets para os campos editáveis
            "nome_personagem": forms.TextInput(
                attrs={"placeholder": "Nome do personagem"}
            ),
            "idade": forms.NumberInput(attrs={"min": 0}),
            "altura": forms.NumberInput(attrs={"step": 0.01}),
            "peso": forms.NumberInput(attrs={"step": 0.01}),
            "tl": forms.NumberInput(attrs={"min": 0}),
            "total_de_pontos": forms.NumberInput(attrs={"min": 0}),
            "pontos_de_experiencia_guardados": forms.NumberInput(attrs={"min": 0}),
            "pontos_de_vantagens": forms.NumberInput(attrs={"min": 0}),
            "pontos_de_desvantagens": forms.NumberInput(attrs={"min": 0}),
            "pontos_de_pericias": forms.NumberInput(attrs={"min": 0}),
            "pontos_de_atributos": forms.NumberInput(attrs={"min": 0}),
            "attributes": forms.Textarea(
                attrs={"rows": 5, "placeholder": "Atributos em formato JSON"}
            ),
            "subattributes": forms.Textarea(
                attrs={"rows": 5, "placeholder": "Subatributos em formato JSON"}
            ),
            "advantages": forms.Textarea(
                attrs={"rows": 5, "placeholder": "Vantagens em formato JSON"}
            ),
            "disadvantages": forms.Textarea(
                attrs={"rows": 5, "placeholder": "Desvantagens em formato JSON"}
            ),
            "skills": forms.Textarea(
                attrs={"rows": 5, "placeholder": "Perícias em formato JSON"}
            ),
            "equipments": forms.Textarea(
                attrs={"rows": 5, "placeholder": "Equipamentos em formato JSON"}
            ),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.get("user")  # Supondo que você passe o usuário no kwargs
        super().__init__(*args, **kwargs)
        if user:
            self.fields["nome_jogador"].initial = (
                user.username
            )  # Definindo o valor automaticamente

    # Validações adicionais
    def clean_nome_personagem(self):
        nome_personagem = self.cleaned_data.get("nome_personagem")
        if not nome_personagem:
            raise forms.ValidationError("Nome do personagem não pode ser vazio")
        return nome_personagem

    def clean_idade(self):
        idade = self.cleaned_data.get("idade")
        if idade is not None and idade < 0:
            raise forms.ValidationError("Idade não pode ser negativa")
        return idade

    def clean_altura(self):
        altura = self.cleaned_data.get("altura")
        if altura is not None and altura <= 0:
            raise forms.ValidationError("Altura deve ser um valor positivo")
        return altura

    def clean_peso(self):
        peso = self.cleaned_data.get("peso")
        if peso is not None and peso <= 0:
            raise forms.ValidationError("Peso deve ser um valor positivo")
        return peso
