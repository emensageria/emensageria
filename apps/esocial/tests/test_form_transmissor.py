from types import SimpleNamespace
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from apps.esocial.forms.transmissor import TransmissorForm


class _FakeTransmissorQuery:

    def __init__(self, all_result):
        self._all_result = all_result

    def exclude(self, **_kwargs):
        return self

    def all(self):
        return self._all_result


class TransmissorFormTests(SimpleTestCase):

    def test_clean_sem_filtro_por_usuario(self):
        form = TransmissorForm()

        with patch("django.forms.ModelForm.clean", return_value={"nrinsc": "123"}), patch(
            "apps.esocial.forms.transmissor.FILTER_BY_USER", False
        ):
            self.assertIsNone(form.clean())

    def test_clean_com_filtro_sem_conflito(self):
        form = TransmissorForm()
        fake_query = _FakeTransmissorQuery(all_result=[])
        fake_transmissor = SimpleNamespace(
            all_objects=SimpleNamespace(filter=lambda **_kw: fake_query)
        )
        current_user = SimpleNamespace(id=9)

        with patch("django.forms.ModelForm.clean", return_value={"nrinsc": "123"}), patch(
            "apps.esocial.forms.transmissor.FILTER_BY_USER", True
        ), patch(
            "apps.esocial.forms.transmissor.get_current_user",
            return_value=current_user,
        ), patch(
            "apps.esocial.forms.transmissor.Transmissor", fake_transmissor
        ):
            self.assertIsNone(form.clean())

    def test_clean_com_filtro_e_conflito_lanca_erro(self):
        form = TransmissorForm()
        fake_query = _FakeTransmissorQuery(all_result=["x"])
        fake_transmissor = SimpleNamespace(
            all_objects=SimpleNamespace(filter=lambda **_kw: fake_query)
        )
        current_user = SimpleNamespace(id=10)

        with patch("django.forms.ModelForm.clean", return_value={"nrinsc": "123"}), patch(
            "apps.esocial.forms.transmissor.FILTER_BY_USER", True
        ), patch(
            "apps.esocial.forms.transmissor.get_current_user",
            return_value=current_user,
        ), patch(
            "apps.esocial.forms.transmissor.Transmissor", fake_transmissor
        ):
            with self.assertRaises(ValidationError):
                form.clean()
