from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from apps.esocial.forms.certificado import CertificadosForm


class CertificadosFormTests(SimpleTestCase):

    def test_save_com_senha_define_valor_e_salva(self):
        form = CertificadosForm()
        form.cleaned_data = {"senha_certificado_input": "segredo"}
        instance = SimpleNamespace(_senha_certificado_input=None, save=Mock())

        with patch("django.forms.ModelForm.save", return_value=instance) as mocked_super:
            result = form.save(commit=True)

        mocked_super.assert_called_once_with(commit=False)
        self.assertIs(result, instance)
        self.assertEqual(instance._senha_certificado_input, "segredo")
        instance.save.assert_called_once_with()

    def test_save_sem_senha_e_sem_commit(self):
        form = CertificadosForm()
        form.cleaned_data = {"senha_certificado_input": ""}
        instance = SimpleNamespace(_senha_certificado_input=None, save=Mock())

        with patch("django.forms.ModelForm.save", return_value=instance):
            result = form.save(commit=False)

        self.assertIs(result, instance)
        self.assertIsNone(instance._senha_certificado_input)
        instance.save.assert_not_called()
