from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.admin.sites import AdminSite
from django.test import SimpleTestCase

from apps.esocial.admin.transmissor import TransmissorAdmin
from apps.esocial.models import Transmissor


class _DummyUser:

    def __init__(self, has_perm_result):
        self._has_perm_result = has_perm_result

    def has_perm(self, _perm):
        return self._has_perm_result


class TransmissorAdminTests(SimpleTestCase):

    def setUp(self):
        self.admin_obj = TransmissorAdmin(Transmissor, AdminSite())

    def test_get_fieldsets_com_permissao_retorna_secao_usuarios(self):
        request = SimpleNamespace(user=_DummyUser(has_perm_result=True))

        with patch(
            "django.contrib.admin.options.ModelAdmin.get_fieldsets",
            return_value=(("Transmissor", {"fields": ("transmissor_tpinsc",)}),),
        ):
            fieldsets = self.admin_obj.get_fieldsets(request)

        self.assertEqual(fieldsets[2][0], "Usuários")
        self.assertEqual(fieldsets[2][1]["fields"], ("users",))

    def test_get_fieldsets_sem_permissao_retorna_super(self):
        request = SimpleNamespace(user=_DummyUser(has_perm_result=False))
        expected = (("Transmissor", {"fields": ("transmissor_tpinsc",)}),)

        with patch(
            "django.contrib.admin.options.ModelAdmin.get_fieldsets",
            return_value=expected,
        ):
            fieldsets = self.admin_obj.get_fieldsets(request)

        self.assertEqual(fieldsets, expected)
