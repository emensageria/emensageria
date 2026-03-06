from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.admin.sites import AdminSite
from django.test import SimpleTestCase

from apps.esocial.admin.certificado import CertificadosAdmin
from apps.esocial.models import Certificados


class _DummyUser:

    def __init__(self, has_perm_result):
        self._has_perm_result = has_perm_result

    def has_perm(self, _perm):
        return self._has_perm_result


class CertificadosAdminTests(SimpleTestCase):

    def setUp(self):
        self.admin_obj = CertificadosAdmin(Certificados, AdminSite())

    def test_get_fieldsets_com_permissao_retorna_secao_usuarios(self):
        request = SimpleNamespace(user=_DummyUser(has_perm_result=True))

        with patch(
            "django.contrib.admin.options.ModelAdmin.get_fieldsets",
            return_value=((None, {"fields": ("nome",)}),),
        ):
            fieldsets = self.admin_obj.get_fieldsets(request)

        self.assertEqual(fieldsets[1][0], "Usuários")
        self.assertEqual(fieldsets[1][1]["fields"], ("users",))

    def test_get_fieldsets_sem_permissao_retorna_super(self):
        request = SimpleNamespace(user=_DummyUser(has_perm_result=False))
        expected = ((None, {"fields": ("nome",)}),)

        with patch(
            "django.contrib.admin.options.ModelAdmin.get_fieldsets",
            return_value=expected,
        ):
            fieldsets = self.admin_obj.get_fieldsets(request)

        self.assertEqual(fieldsets, expected)

    def test_save_model_delega_para_super(self):
        request = SimpleNamespace(user=_DummyUser(has_perm_result=False))
        obj = SimpleNamespace()
        form = SimpleNamespace()

        with patch("django.contrib.admin.options.ModelAdmin.save_model") as mocked_super:
            self.admin_obj.save_model(request, obj, form, change=False)

        mocked_super.assert_called_once_with(request, obj, form, False)
