from django.test import TestCase

from apps.users.models import User, remover_acentos_caracteres_especiais


class UserModelTests(TestCase):

    def test_remover_acentos_caracteres_especiais_remove_simbolos(self):
        self.assertEqual(remover_acentos_caracteres_especiais("João Ç@#!"), "Joao C")

    def test_save_novo_usuario_popula_nomes_e_strings(self):
        user = User(username="usuario_1", name="José Silva")
        user.save()

        self.assertEqual(user.first_name, "José")
        self.assertEqual(user.last_name, "Silva")
        self.assertTrue(user.user_str.endswith(f"({user.username})"))
        self.assertTrue(user.user_search_str.startswith(user.username))
        self.assertIn("Jose", user.user_search_str)

    def test_save_nome_sem_espaco_mantem_nomes_existentes(self):
        user = User(
            username="usuario_2",
            name="Mononome",
            first_name="Primeiro",
            last_name="Ultimo",
        )
        user.save()

        self.assertEqual(user.first_name, "Primeiro")
        self.assertEqual(user.last_name, "Ultimo")

    def test_save_usuario_existente_recalcula_strings(self):
        user = User(username="usuario_3", first_name="Ana", last_name="Moraes")
        user.save()

        user.first_name = "Ana Paula"
        user.save()
        user.refresh_from_db()

        self.assertIn("Ana Paula", user.user_str)
        self.assertIn("usuario_3", user.user_search_str)

    def test_nome_e_str_retornam_valores_esperados(self):
        user = User(username="usuario_4", first_name="Joao", last_name="Souza")
        self.assertEqual(user.nome(), "Joao Souza")
        self.assertEqual(str(user), "Joao Souza")

        user_sem_nome = User(username="usuario_5", first_name="", last_name="")
        self.assertEqual(str(user_sem_nome), "usuario_5")
