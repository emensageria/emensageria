from typing import Any, Dict

from django import forms
from django.core.exceptions import ValidationError

from apps.esocial.choices import EVENTOS, VERSIONS_CODE
from apps.esocial.models import Eventos


class EventosForm(forms.ModelForm):
    current_user = None
    evento_json = forms.JSONField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Eventos
        fields = [
            'versao',
            'evento',
            'operacao',
            'identidade',
            'tpinsc',
            'nrinsc',
            'tpamb',
            'procemi',
            'verproc',
            'status',
            'lote',
            'certificado',
            'evento_json',
        ]

    def clean(
            self):
        cleaned_data: Dict[str, Any] = super().clean() or {}
        versao = cleaned_data.get("versao") or ""
        evento = cleaned_data.get("evento") or ""
        if evento not in VERSIONS_CODE[versao]:
            raise ValidationError(
                "Este evento nao é válido para esta versão do eSocial.")

    def __init__(
            self,
            *args,
            **kwargs):
        super(EventosForm, self).__init__(*args, **kwargs)

        # Acessa os eventos do usuário e filtra as choices do campo `evento`
        if self.current_user and not self.current_user.is_superuser:
            user_eventos = self.current_user.eventos
            # Método para retornar chaves dos eventos selecionados
            filtered_choices = [("", "---------")] + [
                choice for choice in EVENTOS if choice[0] in user_eventos
            ]
            self.fields['evento'].choices = filtered_choices

        self.fields['tpamb'].disabled = True
        self.fields['procemi'].disabled = True
        self.fields['verproc'].disabled = True

        if self.instance.pk:
            self.fields['evento'].disabled = True
            self.fields['versao'].disabled = True
            self.fields['operacao'].disabled = True

        if self.instance.pk and not self.instance.is_aberto:
            for field_name in self.fields:
                self.fields[field_name].disabled = True
