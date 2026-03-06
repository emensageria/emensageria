import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import RequestFactory, SimpleTestCase

from apps.esocial.views.validar_eventos import validar_eventos


class ValidarEventosViewTests(SimpleTestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = SimpleNamespace(is_authenticated=True)

    def test_validar_eventos_processa_todos_e_redireciona(self):
        request = self.factory.get("/esocial/validar-eventos", HTTP_REFERER="/origem")
        request.user = self.user

        evt_sem_lote = SimpleNamespace(
            lote=None,
            vincular_transmissor=MagicMock(),
            validar=MagicMock(),
        )
        evt_com_lote = SimpleNamespace(
            lote=object(),
            vincular_transmissor=MagicMock(),
            validar=MagicMock(),
        )

        with patch(
            "apps.esocial.views.validar_eventos.Eventos.objects.filter",
            return_value=[evt_sem_lote, evt_com_lote],
        ), patch("apps.esocial.views.validar_eventos.verify_domain", return_value=True):
            response = validar_eventos(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/origem")
        evt_sem_lote.vincular_transmissor.assert_called_once()
        evt_com_lote.vincular_transmissor.assert_not_called()
        evt_sem_lote.validar.assert_called_once()
        evt_com_lote.validar.assert_called_once()

    def test_validar_eventos_retorna_json_quando_sem_redirect(self):
        request = self.factory.get("/esocial/validar-eventos", HTTP_REFERER="/origem")
        request.user = self.user

        with patch("apps.esocial.views.validar_eventos.Eventos.objects.filter", return_value=[]), \
                patch("apps.esocial.views.validar_eventos.verify_domain", return_value=False):
            response = validar_eventos(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content.decode()), {})
