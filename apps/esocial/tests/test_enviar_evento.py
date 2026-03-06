import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import RequestFactory, SimpleTestCase

from apps.esocial.views.enviar_evento import enviar_evento


class EnviarEventoViewTests(SimpleTestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = SimpleNamespace(is_authenticated=True)

    def test_enviar_evento_redireciona_quando_referer_valido(self):
        request = self.factory.get("/esocial/enviar-evento/1", HTTP_REFERER="/origem")
        request.user = self.user

        evento = MagicMock()
        evento.enviar.return_value = {"ok": True}

        with patch("apps.esocial.views.enviar_evento.get_object_or_404", return_value=evento), \
                patch("apps.esocial.views.enviar_evento.verify_domain", return_value=True):
            response = enviar_evento(request, 1)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/origem")
        evento.enviar.assert_called_once()

    def test_enviar_evento_retorna_json_quando_sem_redirect(self):
        request = self.factory.get("/esocial/enviar-evento/1", HTTP_REFERER="/origem")
        request.user = self.user

        evento = MagicMock()
        evento.enviar.return_value = {"resultado": "enviado"}

        with patch("apps.esocial.views.enviar_evento.get_object_or_404", return_value=evento), \
                patch("apps.esocial.views.enviar_evento.verify_domain", return_value=False):
            response = enviar_evento(request, 1)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content.decode()), {"resultado": "enviado"})
