from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from apps.esocial.api.viewsets import EventosViewSet
from apps.esocial.choices import (
    STATUS_EVENTO_AGUARD_ENVIO,
    STATUS_EVENTO_ENVIADO,
    STATUS_EVENTO_IMPORTADO,
    STATUS_EVENTO_PROCESSADO,
)


class EventosViewSetTests(SimpleTestCase):

    def test_get_queryset_filtra_por_user_id_e_identidade(self):
        view = EventosViewSet()
        view.request = SimpleNamespace(
            query_params={"user_id": "10", "identidade": "ID1"}
        )
        fake_qs = Mock()
        fake_qs.all.return_value = fake_qs

        with patch(
            "apps.esocial.api.viewsets.Eventos.objects.filter",
            return_value=fake_qs,
        ) as mocked:
            result = view.get_queryset()

        mocked.assert_called_once_with(created_by_id="10", identidade="ID1")
        self.assertIs(result, fake_qs)

    def test_get_queryset_sem_filtros(self):
        view = EventosViewSet()
        view.request = SimpleNamespace(query_params={})
        fake_qs = Mock()
        fake_qs.all.return_value = fake_qs

        with patch(
            "apps.esocial.api.viewsets.Eventos.objects.filter",
            return_value=fake_qs,
        ) as mocked:
            view.get_queryset()

        mocked.assert_called_once_with()

    def test_atualizar_identidade_retorna_payload(self):
        view = EventosViewSet()
        obj = SimpleNamespace(id=1, identidade="ID-NEW", make_identidade=Mock())

        with patch("apps.esocial.api.viewsets.get_object_or_404", return_value=obj) as mocked_get:
            response = view.atualizar_identidade(SimpleNamespace(), pk=1)

        mocked_get.assert_called_once()
        obj.make_identidade.assert_called_once_with()
        self.assertEqual(response.data["id"], 1)
        self.assertEqual(response.data["identidade"], "ID-NEW")

    def test_abrir_evento_para_edicao_retorna_payload(self):
        view = EventosViewSet()
        obj = SimpleNamespace(
            id=2,
            identidade="ID2",
            status=3,
            abrir_evento_para_edicao=Mock(),
            get_status_display=lambda: "Status",
        )

        with patch("apps.esocial.api.viewsets.get_object_or_404", return_value=obj):
            response = view.abrir_evento_para_edicao(SimpleNamespace(), pk=2)

        obj.abrir_evento_para_edicao.assert_called_once_with()
        self.assertEqual(response.data["status_txt"], "Status")

    def test_validar_vincula_quando_sem_lote(self):
        view = EventosViewSet()
        first = SimpleNamespace(
            id=3,
            identidade="ID3",
            lote=None,
            vincular_transmissor=Mock(),
            create_xml=Mock(),
            validar=Mock(),
        )
        second = SimpleNamespace(
            id=3,
            identidade="ID3",
            status=5,
            get_status_display=lambda: "OK",
            ocorrencias_json={"x": 1},
        )

        with patch("apps.esocial.api.viewsets.get_object_or_404", side_effect=[first, second]):
            response = view.validar(SimpleNamespace(), pk=3)

        first.vincular_transmissor.assert_called_once_with()
        first.create_xml.assert_called_once_with()
        first.validar.assert_called_once_with()
        self.assertEqual(response.data["ocorrencias"], {"x": 1})

    def test_validar_sem_vinculo_quando_com_lote(self):
        view = EventosViewSet()
        first = SimpleNamespace(
            id=4,
            identidade="ID4",
            lote=object(),
            vincular_transmissor=Mock(),
            create_xml=Mock(),
            validar=Mock(),
        )
        second = SimpleNamespace(
            id=4,
            identidade="ID4",
            status=5,
            get_status_display=lambda: "OK",
            ocorrencias_json=None,
        )

        with patch("apps.esocial.api.viewsets.get_object_or_404", side_effect=[first, second]):
            response = view.validar(SimpleNamespace(), pk=4)

        first.vincular_transmissor.assert_not_called()
        self.assertEqual(response.data["ocorrencias"], {})

    def test_enviar_quando_status_permitido(self):
        view = EventosViewSet()
        first = SimpleNamespace(
            id=5,
            identidade="ID5",
            status=STATUS_EVENTO_AGUARD_ENVIO,
            ocorrencias_json={},
            retorno_envio_json={"a": 1},
            get_status_display=lambda: "Aguardando",
            enviar=Mock(
                return_value={"retorno": "ok", "mensagem": "feito", "retorno_envio": {"r": 1}}
            ),
        )
        second = SimpleNamespace(
            id=5,
            identidade="ID5",
            status=STATUS_EVENTO_PROCESSADO,
            ocorrencias_json=None,
            retorno_envio_json={"b": 2},
            get_status_display=lambda: "Processado",
        )

        with patch("apps.esocial.api.viewsets.get_object_or_404", side_effect=[first, second]):
            response = view.enviar(SimpleNamespace(), pk=5)

        first.enviar.assert_called_once_with()
        self.assertEqual(response.data["retorno"], "ok")
        self.assertEqual(response.data["retorno_envio_lote"], {"r": 1})
        self.assertEqual(response.data["retorno_envio"], {"b": 2})

    def test_enviar_quando_status_nao_permitido(self):
        view = EventosViewSet()
        obj = SimpleNamespace(id=6, status=STATUS_EVENTO_ENVIADO)

        with patch("apps.esocial.api.viewsets.get_object_or_404", return_value=obj):
            response = view.enviar(SimpleNamespace(), pk=6)

        self.assertEqual(response.data["retorno"], "error")

    def test_consultar_quando_status_permitido(self):
        view = EventosViewSet()
        first = SimpleNamespace(
            id=7,
            identidade="ID7",
            status=STATUS_EVENTO_ENVIADO,
            ocorrencias_json={"z": 1},
            retorno_consulta_json={"x": 1},
            get_status_display=lambda: "Enviado",
            consultar=Mock(
                return_value={
                    "retorno": "ok",
                    "mensagem": "consultado",
                    "retorno_consulta": {"y": 2},
                }
            ),
        )
        second = SimpleNamespace(
            id=7,
            identidade="ID7",
            status=STATUS_EVENTO_PROCESSADO,
            ocorrencias_json=None,
            retorno_consulta_json={"k": 3},
            get_status_display=lambda: "Processado",
        )

        with patch("apps.esocial.api.viewsets.get_object_or_404", side_effect=[first, second]):
            response = view.consultar(SimpleNamespace(), pk=7)

        first.consultar.assert_called_once_with()
        self.assertEqual(response.data["retorno"], "ok")
        self.assertEqual(response.data["retorno_consulta_lote"], {"y": 2})
        self.assertEqual(response.data["retorno_consulta"], {"k": 3})

    def test_consultar_quando_status_nao_permitido(self):
        view = EventosViewSet()
        obj = SimpleNamespace(id=8, status=STATUS_EVENTO_IMPORTADO)

        with patch("apps.esocial.api.viewsets.get_object_or_404", return_value=obj):
            response = view.consultar(SimpleNamespace(), pk=8)

        self.assertEqual(response.data["retorno"], "error")
