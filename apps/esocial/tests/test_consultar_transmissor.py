import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import RequestFactory, SimpleTestCase

from apps.esocial.views.consultar_transmissor import consultar_transmissor


class ConsultarTransmissorViewTests(SimpleTestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = SimpleNamespace(is_authenticated=True)

    def test_consultar_transmissor_redireciona_quando_referer_valido(self):
        request = self.factory.get("/esocial/consultar-transmissor/1", HTTP_REFERER="/origem")
        request.user = self.user

        transmissor = MagicMock()
        transmissor.consultar.return_value = {"ok": True}

        with patch(
            "apps.esocial.views.consultar_transmissor.get_object_or_404",
            return_value=transmissor,
        ), patch("apps.esocial.views.consultar_transmissor.verify_domain", return_value=True):
            response = consultar_transmissor(request, 1)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/origem")
        transmissor.consultar.assert_called_once()

    def test_consultar_transmissor_retorna_json_quando_sem_redirect(self):
        request = self.factory.get("/esocial/consultar-transmissor/1", HTTP_REFERER="/origem")
        request.user = self.user

        transmissor = MagicMock()
        transmissor.consultar.return_value = {"resultado": "ok"}

        with patch(
            "apps.esocial.views.consultar_transmissor.get_object_or_404",
            return_value=transmissor,
        ), patch("apps.esocial.views.consultar_transmissor.verify_domain", return_value=False):
            response = consultar_transmissor(request, 1)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content.decode()), {"resultado": "ok"})
