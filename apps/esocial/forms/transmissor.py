from django import forms
from django.core.exceptions import ValidationError
from django_currentuser.middleware import get_current_user

from apps.esocial.models import Transmissor
from config.settings import FILTER_BY_USER


class TransmissorForm(forms.ModelForm):
    class Meta:
        model = Transmissor
        fields = [
            'transmissor_tpinsc',
            'transmissor_nrinsc',
            'nome_empresa',
            'logotipo',
            'endereco_completo',
            'tpinsc',
            'nrinsc',
            'certificado',
            'users',
        ]

    def clean(self):
        cleaned_data = super().clean() or {}
        nrinsc = cleaned_data.get("nrinsc")
        if FILTER_BY_USER:
            current_user = get_current_user()
            transmissores = Transmissor.all_objects. \
                filter(nrinsc=nrinsc). \
                exclude(created_by=current_user). \
                exclude(users__id=current_user.id).all()
            if transmissores:
                raise ValidationError(
                    "Já existe um transmissor cadastrado com este número. '"
                    "'Entre em contato com o administrador do sistema e '"
                    "'solicite que vincule ele ao seu usuário.")
