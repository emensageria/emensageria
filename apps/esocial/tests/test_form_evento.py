from types import SimpleNamespace
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.esocial.forms.evento import EventosForm
from apps.esocial.models import Eventos


class EventosFormTests(TestCase):

    def tearDown(self):
        EventosForm.current_user = None

    def test_clean_valido(self):
        form = EventosForm()

        with patch(
            "django.forms.ModelForm.clean",
            return_value={"versao": "v_S_01_03_00", "evento": "s1000"},
        ):
            self.assertIsNone(form.clean())

    def test_clean_invalido(self):
        form = EventosForm()

        with patch(
            "django.forms.ModelForm.clean",
            return_value={"versao": "v_S_01_03_00", "evento": "nao-existe"},
        ):
            with self.assertRaises(ValidationError):
                form.clean()

    def test_init_filtra_choices_para_usuario_nao_superuser(self):
        EventosForm.current_user = SimpleNamespace(is_superuser=False, eventos=["s1000"])

        form = EventosForm(instance=Eventos(evento="s1000", tpinsc=1, nrinsc="123"))

        choices = form.fields["evento"].choices
        expected_choice = (
            "s1000",
            "S-1000 - Informações do Empregador/Contribuinte/Órgão Público",
        )
        self.assertEqual(choices[0], ("", "---------"))
        self.assertIn(expected_choice, choices)
        self.assertTrue(form.fields["tpamb"].disabled)
        self.assertTrue(form.fields["procemi"].disabled)
        self.assertTrue(form.fields["verproc"].disabled)

    def test_init_desabilita_campos_quando_instancia_tem_pk(self):
        instance = Eventos(pk=10, evento="s1000", tpinsc=1, nrinsc="123", is_aberto=True)

        form = EventosForm(instance=instance)

        self.assertTrue(form.fields["evento"].disabled)
        self.assertTrue(form.fields["versao"].disabled)
        self.assertTrue(form.fields["operacao"].disabled)

    def test_init_desabilita_todos_campos_quando_instancia_fechada(self):
        instance = Eventos(pk=11, evento="s1000", tpinsc=1, nrinsc="123", is_aberto=False)

        form = EventosForm(instance=instance)

        self.assertTrue(all(field.disabled for field in form.fields.values()))
