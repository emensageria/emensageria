from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import RequestFactory, SimpleTestCase

from apps.esocial.views.consultar_transmissores import consultar_transmissores


class ConsultarTransmissoresViewTests(SimpleTestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = SimpleNamespace(is_authenticated=True)

    def test_consultar_transmissores_consulta_lotes_e_redireciona(self):
        request = self.factory.get("/esocial/consultar-transmissores", HTTP_REFERER="/voltar")
        request.user = self.user

        lote_1 = SimpleNamespace(consultar=MagicMock())
        lote_2 = SimpleNamespace(consultar=MagicMock())
        queryset = MagicMock()
        queryset.all.return_value = [lote_1, lote_2]

        with patch(
            "apps.esocial.views.consultar_transmissores.Lotes.objects.filter",
            return_value=queryset,
        ), patch(
            "apps.esocial.views.consultar_transmissores.verify_domain",
            return_value=True,
        ), patch("apps.esocial.views.consultar_transmissores.messages.success") as success_mock:
            response = consultar_transmissores(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/voltar")
        lote_1.consultar.assert_called_once()
        lote_2.consultar.assert_called_once()
        success_mock.assert_called_once()

    def test_consultar_transmissores_retorna_json_quando_sem_redirect(self):
        request = self.factory.get("/esocial/consultar-transmissores", HTTP_REFERER="/voltar")
        request.user = self.user

        lote = SimpleNamespace(consultar=MagicMock())
        queryset = MagicMock()
        queryset.all.return_value = [lote]

        with patch(
            "apps.esocial.views.consultar_transmissores.Lotes.objects.filter",
            return_value=queryset,
        ), patch("apps.esocial.views.consultar_transmissores.verify_domain", return_value=False):
            response = consultar_transmissores(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), '{"mensagem": "Lotes consultados"}')
