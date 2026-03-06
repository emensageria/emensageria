import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import RequestFactory, SimpleTestCase

from apps.esocial.views.consultar_evento import consultar_evento


class ConsultarEventoViewTests(SimpleTestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = SimpleNamespace(is_authenticated=True)

    def test_consultar_evento_vincula_e_redireciona_quando_referer_valido(self):
        request = self.factory.get("/esocial/consultar-evento/1", HTTP_REFERER="/origem")
        request.user = self.user

        lote = MagicMock()
        lote.consultar.return_value = {"ok": True}
        evento = SimpleNamespace(lote=None)

        def set_lote():
            evento.lote = lote

        evento.vincular_transmissor = MagicMock(side_effect=set_lote)

        with patch("apps.esocial.views.consultar_evento.get_object_or_404", return_value=evento), \
                patch("apps.esocial.views.consultar_evento.verify_domain", return_value=True):
            response = consultar_evento(request, 1)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/origem")
        evento.vincular_transmissor.assert_called_once()
        lote.consultar.assert_called_once()

    def test_consultar_evento_retorna_erro_json_quando_sem_lote(self):
        request = self.factory.get("/esocial/consultar-evento/1", HTTP_REFERER="/origem")
        request.user = self.user

        evento = SimpleNamespace(lote=None, vincular_transmissor=MagicMock())

        with patch("apps.esocial.views.consultar_evento.get_object_or_404", return_value=evento), \
                patch("apps.esocial.views.consultar_evento.verify_domain", return_value=False), \
                patch("apps.esocial.views.consultar_evento.messages.error") as error_mock:
            response = consultar_evento(request, 1)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content.decode()),
            {"error": "Transmissor não vinculado ao evento"},
        )
        error_mock.assert_called_once()
        evento.vincular_transmissor.assert_called_once()

    def test_consultar_evento_redireciona_no_fluxo_de_erro_com_referer_valido(self):
        request = self.factory.get("/esocial/consultar-evento/1", HTTP_REFERER="/origem")
        request.user = self.user

        evento = SimpleNamespace(lote=None, vincular_transmissor=MagicMock())

        with patch("apps.esocial.views.consultar_evento.get_object_or_404", return_value=evento), \
                patch("apps.esocial.views.consultar_evento.verify_domain", return_value=True), \
                patch("apps.esocial.views.consultar_evento.messages.error"):
            response = consultar_evento(request, 1)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/origem")

    def test_consultar_evento_retorna_resposta_json_quando_sem_referer(self):
        request = self.factory.get("/esocial/consultar-evento/1")
        request.user = self.user

        lote = MagicMock()
        lote.consultar.return_value = {"resultado": "ok"}
        evento = SimpleNamespace(lote=lote, vincular_transmissor=MagicMock())

        with patch("apps.esocial.views.consultar_evento.get_object_or_404", return_value=evento):
            response = consultar_evento(request, 1)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content.decode()), {"resultado": "ok"})
        evento.vincular_transmissor.assert_not_called()
