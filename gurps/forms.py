from django.forms import ModelForm
from django import forms
from .models import *
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
            "pontos_de_ficha",
            "pontos_de_desvantagens",
            "tl",
            "descricao",
            "regras",
            "imagem",
        ]
        widgets = {
            "descricao": forms.Textarea(attrs={"rows": 4, "cols": 40}),
            "regras": forms.Textarea(attrs={"rows": 4, "cols": 40}),
        }


class CampanhaAssetsForm(forms.ModelForm):
    class Meta:
        model = CampanhaAssets
        fields = ["name", "description", "show", "image"]  # Corrigida a vírgula ausente
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "show": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),  # Adicionado campo 'show'
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control-file"}),
        }

    def __init__(self, *args, campanha=None, **kwargs):
        super().__init__(*args, **kwargs)
        if campanha:
            self.fields["campanha"] = forms.ModelChoiceField(
                queryset=Campanha.objects.filter(id=campanha.id),
                initial=campanha,
                widget=forms.HiddenInput(),  # Mantém a campanha oculta para garantir que não seja editável
            )


class CharacterSheetForm(forms.ModelForm):
    class Meta:
        model = CharacterSheet
        fields = [
            "info_campanha",
            "nome_personagem",
            "aparencia_idade",
            "pontos_soma",
            "atributos",
            "sub_attributes",
            "advantages",
            "disadvantages",
            "skills",
            "money",
            "background",
            "photo",
            "equipment_melee",
            "equipment_ranged",
            "equipment_armor",
            "maneuvers_melee",
            "maneuvers_ranged",
            "maneuvers_defense",
        ]
        widgets = {
            "aparencia_idade": forms.Textarea(
                attrs={"placeholder": 'JSON format: {"appearance": "", "age": ""}'}
            ),
            "pontos_soma": forms.Textarea(
                attrs={"placeholder": "JSON format for points summary"}
            ),
            "atributos": forms.Textarea(
                attrs={"placeholder": "JSON format for atributos"}
            ),
            "sub_attributes": forms.Textarea(
                attrs={"placeholder": "JSON format for sub-attributes"}
            ),
            "advantages": forms.Textarea(
                attrs={"placeholder": "JSON list format for advantages"}
            ),
            "disadvantages": forms.Textarea(
                attrs={"placeholder": "JSON list format for disadvantages"}
            ),
            "skills": forms.Textarea(
                attrs={"placeholder": "JSON list format for skills"}
            ),
            "equipment_melee": forms.Textarea(
                attrs={"placeholder": "JSON list format for melee equipment"}
            ),
            "equipment_ranged": forms.Textarea(
                attrs={"placeholder": "JSON list format for ranged equipment"}
            ),
            "equipment_armor": forms.Textarea(
                attrs={"placeholder": "JSON list format for armor equipment"}
            ),
            "maneuvers_melee": forms.Textarea(
                attrs={"placeholder": "JSON list format for melee maneuvers"}
            ),
            "maneuvers_ranged": forms.Textarea(
                attrs={"placeholder": "JSON list format for ranged maneuvers"}
            ),
            "maneuvers_defense": forms.Textarea(
                attrs={"placeholder": "JSON list format for defense maneuvers"}
            ),
        }
