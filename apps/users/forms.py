# forms.py
from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import User

COMMON_LABELS = {
    "username": "Nome do usuário",
    "name": "Nome Completo",
    "is_staff": "Acessa o sistema?",
    "is_superuser": "É administrador?",
    "is_active": "Está ativo?",
    "groups": "Grupos",
}


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = (
            "username", "name", "is_staff", "is_superuser",
            "is_active", "groups", "eventos")
        labels = COMMON_LABELS.copy()


class CustomUserChangeForm(UserChangeForm):

    class Meta:
        model = User
        fields = (
            "username", "name", "is_staff", "is_superuser",
            "is_active", "groups",
            "eventos")
        labels = COMMON_LABELS.copy()


# Form geral para CRUD customizado
class UserForm(forms.ModelForm):

    class Meta:
        model = User
        fields = [
            "username", "name", "is_staff", "is_superuser",
            "is_active", "groups",
            "eventos"]
        labels = COMMON_LABELS.copy()
