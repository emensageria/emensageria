from django.test import SimpleTestCase

from apps.esocial.choices import (
    CHOICES_PRODUCTION,
    CODIGOS_RESPOSTA_ERROS,
    STATUS_EVENTO_AGUARD_ENVIO,
    STATUS_EVENTO_CADASTRADO,
    STATUS_EVENTO_ENVIADO,
    STATUS_EVENTO_ERRO,
    STATUS_EVENTO_IMPORTADO,
    STATUS_EVENTO_PROCESSADO,
)
from config import settings
from config.context_processors import admin_media


class ContextProcessorTests(SimpleTestCase):

    def test_admin_media_returns_expected_payload(self):
        payload = admin_media(request=None)

        self.assertEqual(payload["DEBUG"], settings.DEBUG)
        self.assertEqual(payload["VERSAO_EMENSAGERIA"], settings.VERSAO_EMENSAGERIA)
        self.assertEqual(payload["DATABASE_NAME"], settings.DATABASES["default"]["NAME"])
        self.assertEqual(payload["MEDIA_URL"], settings.MEDIA_URL)
        self.assertEqual(payload["LINK_WEBSITE"], settings.LINK_WEBSITE)
        self.assertEqual(payload["STATUS_EVENTO_CADASTRADO"], STATUS_EVENTO_CADASTRADO)
        self.assertEqual(payload["STATUS_EVENTO_IMPORTADO"], STATUS_EVENTO_IMPORTADO)
        self.assertEqual(payload["STATUS_EVENTO_AGUARD_ENVIO"], STATUS_EVENTO_AGUARD_ENVIO)
        self.assertEqual(payload["STATUS_EVENTO_ENVIADO"], STATUS_EVENTO_ENVIADO)
        self.assertEqual(payload["STATUS_EVENTO_ERRO"], STATUS_EVENTO_ERRO)
        self.assertEqual(payload["STATUS_EVENTO_PROCESSADO"], STATUS_EVENTO_PROCESSADO)
        self.assertEqual(payload["CODIGOS_RESPOSTA_ERROS"], CODIGOS_RESPOSTA_ERROS)
        self.assertEqual(payload["CHOICES_PRODUCTION"], CHOICES_PRODUCTION)
        self.assertEqual(payload["ESOCIAL_TPAMB"], settings.ESOCIAL_TPAMB)
        self.assertIn("hoje", payload)
