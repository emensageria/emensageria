from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import RequestFactory, SimpleTestCase

from apps.esocial.views.visualizar_xml import visualizar_xml


class VisualizarXmlViewTests(SimpleTestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = SimpleNamespace(is_authenticated=True)

    def test_visualizar_xml_vincula_transmissor_quando_sem_lote(self):
        request = self.factory.get("/esocial/visualizar-xml/1")
        request.user = self.user

        evento = SimpleNamespace(
            lote=None,
            vincular_transmissor=MagicMock(),
            create_xml=MagicMock(),
            evento_xml="<xml>ok</xml>",
        )

        with patch("apps.esocial.views.visualizar_xml.get_object_or_404", return_value=evento):
            response = visualizar_xml(request, 1)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "<xml>ok</xml>")
        evento.vincular_transmissor.assert_called_once()
        evento.create_xml.assert_called_once()

    def test_visualizar_xml_nao_vincula_quando_ja_tem_lote(self):
        request = self.factory.get("/esocial/visualizar-xml/1")
        request.user = self.user

        evento = SimpleNamespace(
            lote=object(),
            vincular_transmissor=MagicMock(),
            create_xml=MagicMock(),
            evento_xml="<xml>ok</xml>",
        )

        with patch("apps.esocial.views.visualizar_xml.get_object_or_404", return_value=evento):
            response = visualizar_xml(request, 1)

        self.assertEqual(response.status_code, 200)
        evento.vincular_transmissor.assert_not_called()
        evento.create_xml.assert_called_once()
