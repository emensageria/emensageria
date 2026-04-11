from io import StringIO
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings


@override_settings(
    SUPERUSER_USERNAME="admin",
    SUPERUSER_PASSWORD="admin",
    SUPERUSER_EMAIL="admin@localhost",
)
class CreateSuperuserIfNoneCommandTests(TestCase):

    def test_command_creates_default_superuser(self):
        user_model = get_user_model()

        call_command("create_superuser_if_none")

        user = user_model.objects.get(username="admin")
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.check_password("admin"))
        self.assertEqual(user.email, "admin@localhost")

    def test_command_promotes_existing_user_without_superuser(self):
        user_model = get_user_model()
        user = user_model.objects.create(username="admin", is_staff=False, is_superuser=False)
        user.set_password("senha-antiga")
        user.save()

        call_command("create_superuser_if_none")

        user.refresh_from_db()
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.check_password("admin"))

    def test_command_keeps_existing_superuser(self):
        user_model = get_user_model()
        user_model.objects.create_superuser(username="root", password="senha-forte")

        call_command("create_superuser_if_none")

        self.assertEqual(user_model.objects.filter(is_superuser=True).count(), 1)


class EsocialConsultarCommandTests(TestCase):

    def test_command_runs_without_invalid_field_lookup(self):
        call_command("esocial_consultar")

    def test_command_consults_and_prints_matching_lotes(self):
        lote = SimpleNamespace(
            id=7,
            status=3,
            resposta_codigo="201",
            resposta_descricao="OK",
            consultar=MagicMock(),
        )
        stdout = StringIO()

        with patch(
            "apps.esocial.management.commands.esocial_consultar.Lotes.objects.filter",
            return_value=[lote],
        ):
            call_command("esocial_consultar", stdout=stdout)

        lote.consultar.assert_called_once()
        self.assertIn("7 3 201 OK", stdout.getvalue())
