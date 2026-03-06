from unittest.mock import patch

from cryptography.fernet import Fernet
from django.conf import settings
from django.test import SimpleTestCase

from apps.esocial.models.certificado import Certificados, get_cipher


class CertificadosModelTests(SimpleTestCase):

    def test_get_cipher_retorna_fernet_funcional(self):
        cipher = get_cipher()

        self.assertIsInstance(cipher, Fernet)
        token = cipher.encrypt(b"abc")
        self.assertEqual(cipher.decrypt(token), b"abc")

    def test_save_com_senha_criptografa_e_get_senha_descriptografa(self):
        cert = Certificados(nome="Meu Cert")
        cert._senha_certificado_input = "senha123"

        with patch("config.mixins.BaseModelEsocial.save") as mocked_super:
            cert.save()

        mocked_super.assert_called_once_with()
        self.assertIsNotNone(cert.senha_certificado)
        self.assertEqual(cert.get_senha_certificado(), "senha123")
        self.assertEqual(cert.get_senha(), "senha123")

    def test_save_sem_senha_preserva_valor(self):
        cert = Certificados(nome="Meu Cert", senha_certificado="valor-antigo")
        cert._senha_certificado_input = None

        with patch("config.mixins.BaseModelEsocial.save"):
            cert.save()

        self.assertEqual(cert.senha_certificado, "valor-antigo")

    def test_get_senha_certificado_invalido_retorna_none(self):
        cert = Certificados(nome="Meu Cert", senha_certificado="@@invalido@@")

        self.assertIsNone(cert.get_senha_certificado())

    def test_get_senha_certificado_vazio_retorna_none(self):
        cert = Certificados(nome="Meu Cert", senha_certificado=None)

        self.assertIsNone(cert.get_senha_certificado())

    def test_cert_host_retorna_caminho_absoluto(self):
        cert = Certificados(nome="Meu Cert")
        cert.certificado = "arquivo.pfx"

        expected = f"{settings.BASE_DIR}/{settings.CERT_PATH}/arquivo.pfx".replace("//", "/")
        self.assertEqual(cert.cert_host().replace("//", "/"), expected)

    def test_str_retorna_nome(self):
        cert = Certificados(nome="Nome Cert")

        self.assertEqual(str(cert), "Nome Cert")
