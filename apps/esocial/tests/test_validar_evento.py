from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import RequestFactory, SimpleTestCase

from apps.esocial.views.validar_evento import validar_evento


class ValidarEventoViewTests(SimpleTestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = SimpleNamespace(is_authenticated=True)

    def test_validar_evento_com_json_sem_lote_vincula_recarrega_valida_e_redireciona(self):
        request = self.factory.get("/esocial/validar-evento/1", HTTP_REFERER="/origem")
        request.user = self.user

        evento_inicial = SimpleNamespace(
            evento_json='{"a": 1}',
            lote=None,
            vincular_transmissor=MagicMock(),
            identidade="ID1",
        )
        evento_atualizado = SimpleNamespace(validar=MagicMock())

        with patch(
            "apps.esocial.views.validar_evento.get_object_or_404",
            return_value=evento_inicial,
        ), patch(
            "apps.esocial.views.validar_evento.Eventos.objects.get",
            return_value=evento_atualizado,
        ), patch("apps.esocial.views.validar_evento.verify_domain", return_value=True):
            response = validar_evento(request, 1)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/origem")
        evento_inicial.vincular_transmissor.assert_called_once()
        evento_atualizado.validar.assert_called_once()

    def test_validar_evento_com_json_e_lote_valida_sem_recarregar(self):
        request = self.factory.get("/esocial/validar-evento/1")
        request.user = self.user

        evento = SimpleNamespace(
            evento_json='{"a": 1}',
            lote=object(),
            validar=MagicMock(),
            vincular_transmissor=MagicMock(),
            identidade="ID1",
        )

        with patch("apps.esocial.views.validar_evento.get_object_or_404", return_value=evento):
            response = validar_evento(request, 1)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "{}")
        evento.vincular_transmissor.assert_not_called()
        evento.validar.assert_called_once()

    def test_validar_evento_sem_json_adiciona_mensagem_erro(self):
        request = self.factory.get("/esocial/validar-evento/1", HTTP_REFERER="/origem")
        request.user = self.user

        evento = SimpleNamespace(
            evento_json="",
            lote=None,
            validar=MagicMock(),
            vincular_transmissor=MagicMock(),
            identidade="ID-SEM-DADOS",
        )

        with patch("apps.esocial.views.validar_evento.get_object_or_404", return_value=evento), \
                patch("apps.esocial.views.validar_evento.verify_domain", return_value=False), \
                patch("apps.esocial.views.validar_evento.messages.add_message") as add_message_mock:
            response = validar_evento(request, 1)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "{}")
        add_message_mock.assert_called_once()
        evento.validar.assert_not_called()
