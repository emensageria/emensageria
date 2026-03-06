from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import RequestFactory, SimpleTestCase

from apps.esocial.views.enviar_transmissores import enviar_transmissores


class EnviarTransmissoresViewTests(SimpleTestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = SimpleNamespace(is_authenticated=True)

    def test_enviar_transmissores_processa_e_redireciona(self):
        request = self.factory.get("/esocial/enviar-transmissores", HTTP_REFERER="/voltar")
        request.user = self.user

        fila_cadastrada = MagicMock()
        fila_aguardando = MagicMock()
        lote_1 = SimpleNamespace(enviar=MagicMock())
        lote_2 = SimpleNamespace(enviar=MagicMock())
        fila_aguardando.all.return_value = [lote_1, lote_2]

        evento_1 = SimpleNamespace(vincular_transmissor=MagicMock())
        evento_2 = SimpleNamespace(vincular_transmissor=MagicMock())

        with patch(
            "apps.esocial.views.enviar_transmissores.Lotes.objects.filter",
            side_effect=[fila_cadastrada, fila_aguardando],
        ), patch(
            "apps.esocial.views.enviar_transmissores.Eventos.objects.filter",
            return_value=[evento_1, evento_2],
        ), patch("apps.esocial.views.enviar_transmissores.verify_domain", return_value=True), \
                patch("apps.esocial.views.enviar_transmissores.messages.success") as success_mock:
            response = enviar_transmissores(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/voltar")
        fila_cadastrada.update.assert_called_once()
        evento_1.vincular_transmissor.assert_called_once()
        evento_2.vincular_transmissor.assert_called_once()
        lote_1.enviar.assert_called_once()
        lote_2.enviar.assert_called_once()
        success_mock.assert_called_once()

    def test_enviar_transmissores_retorna_json_quando_sem_redirect(self):
        request = self.factory.get("/esocial/enviar-transmissores", HTTP_REFERER="/voltar")
        request.user = self.user

        fila_cadastrada = MagicMock()
        fila_aguardando = MagicMock()
        fila_aguardando.all.return_value = []

        with patch(
            "apps.esocial.views.enviar_transmissores.Lotes.objects.filter",
            side_effect=[fila_cadastrada, fila_aguardando],
        ), patch(
            "apps.esocial.views.enviar_transmissores.Eventos.objects.filter",
            return_value=[],
        ), patch("apps.esocial.views.enviar_transmissores.verify_domain", return_value=False):
            response = enviar_transmissores(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), '{"mensagem": "Lotes enviados"}')
