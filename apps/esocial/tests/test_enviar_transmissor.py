import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import RequestFactory, SimpleTestCase

from apps.esocial.views.enviar_transmissor import enviar_transmissor


class EnviarTransmissorViewTests(SimpleTestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = SimpleNamespace(is_authenticated=True)

    def test_enviar_transmissor_redireciona_quando_referer_valido(self):
        request = self.factory.get("/esocial/enviar-transmissor/1", HTTP_REFERER="/origem")
        request.user = self.user

        transmissor = MagicMock()
        transmissor.enviar.return_value = {"ok": True}

        with patch(
            "apps.esocial.views.enviar_transmissor.get_object_or_404",
            return_value=transmissor,
        ), patch("apps.esocial.views.enviar_transmissor.verify_domain", return_value=True):
            response = enviar_transmissor(request, 1)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/origem")
        transmissor.enviar.assert_called_once()

    def test_enviar_transmissor_retorna_json_quando_sem_redirect(self):
        request = self.factory.get("/esocial/enviar-transmissor/1", HTTP_REFERER="/origem")
        request.user = self.user

        transmissor = MagicMock()
        transmissor.enviar.return_value = {"resultado": "enviado"}

        with patch(
            "apps.esocial.views.enviar_transmissor.get_object_or_404",
            return_value=transmissor,
        ), patch("apps.esocial.views.enviar_transmissor.verify_domain", return_value=False):
            response = enviar_transmissor(request, 1)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content.decode()), {"resultado": "enviado"})
