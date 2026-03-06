from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.admin.sites import AdminSite
from django.http import HttpResponseRedirect
from django.test import SimpleTestCase

from apps.esocial.admin.evento import (
    EventosAdmin,
    convert_form_data_to_json,
    set_nested_value,
)
from apps.esocial.choices import (
    STATUS_EVENTO_AGUARD_ENVIO,
    STATUS_EVENTO_CADASTRADO,
    STATUS_EVENTO_ENVIADO,
    STATUS_EVENTO_ERRO,
    STATUS_EVENTO_IMPORTADO,
    STATUS_EVENTO_PROCESSADO,
)
from apps.esocial.models import Eventos


class _FakeQuerySet:

    def __init__(self):
        self.filtered_kwargs = {}

    def filter(self, **kwargs):
        self.filtered_kwargs = kwargs
        return self


class EventosAdminTests(SimpleTestCase):

    def setUp(self):
        self.admin_obj = EventosAdmin(Eventos, AdminSite())

    def test_set_nested_value_suporta_dict_e_lista(self):
        payload = {}

        set_nested_value(payload, ["eSocial", "evt", "id"], "A")
        set_nested_value(payload, ["eSocial", "itens[]"], "x")
        set_nested_value(payload, ["eSocial", "itens[]"], "y")

        self.assertEqual(payload["eSocial"]["evt"]["id"], "A")
        self.assertEqual(payload["eSocial"]["itens"], ["x", "y"])

    def test_convert_form_data_to_json_converte_chaves_aninhadas(self):
        form_data = {
            "eSocial[evt][id]": ["EVT1"],
            "eSocial[itens[]]": ["A"],
        }

        data = convert_form_data_to_json(form_data)

        self.assertEqual(data["eSocial"]["evt"]["id"], "EVT1")
        self.assertEqual(data["eSocial"]["itens"], {"": "A"})

    def test_get_protocolo_retorna_valor_ou_vazio(self):
        com_retorno = SimpleNamespace(
            retorno_envio_lote=lambda: {"dadosRecepcaoLote": {"protocoloEnvio": "P123"}}
        )
        sem_retorno = SimpleNamespace(retorno_envio_lote=lambda: None)

        self.assertEqual(self.admin_obj.get_protocolo(com_retorno), "P123")
        self.assertEqual(self.admin_obj.get_protocolo(sem_retorno), "")

    def test_get_nr_recibo_retorna_valor_ou_vazio(self):
        com_retorno = SimpleNamespace(
            retorno_consulta_lote=lambda: {
                "retornoEvento": {
                    "eSocial": {"retornoEvento": {"recibo": {"nrRecibo": "R999"}}}
                }
            }
        )
        sem_retorno = SimpleNamespace(retorno_consulta_lote=lambda: None)

        self.assertEqual(self.admin_obj.get_nr_recibo(com_retorno), "R999")
        self.assertEqual(self.admin_obj.get_nr_recibo(sem_retorno), "")

    def test_acoes_retorna_html_por_status(self):
        casos = [
            (STATUS_EVENTO_CADASTRADO, "Validar"),
            (STATUS_EVENTO_IMPORTADO, "Validar"),
            (STATUS_EVENTO_ERRO, "Corrigir"),
            (STATUS_EVENTO_AGUARD_ENVIO, "Enviar"),
            (STATUS_EVENTO_ENVIADO, "Consultar"),
            (STATUS_EVENTO_PROCESSADO, "Consultar"),
        ]

        with patch(
            "django.urls.reverse",
            side_effect=lambda name, kwargs=None: (
                "/%s/%s" % (name, (kwargs or {}).get("pk") or (kwargs or {}).get("object_id"))
            ),
        ):
            for status, texto in casos:
                with self.subTest(status=status):
                    html = self.admin_obj.acoes(SimpleNamespace(status=status, pk=10))
                    self.assertIn(texto, html)

    def test_acoes_retorna_vazio_para_status_desconhecido(self):
        html = self.admin_obj.acoes(SimpleNamespace(status=999, pk=10))

        self.assertEqual(html, "")

    def test_atualizar_identidade_atualiza_apenas_status_permitido(self):
        permitido = SimpleNamespace(
            status=STATUS_EVENTO_CADASTRADO,
            identidade="OLD",
            make_identidade=Mock(return_value="NEW"),
            save=Mock(),
        )
        bloqueado = SimpleNamespace(
            status=STATUS_EVENTO_ENVIADO,
            make_identidade=Mock(),
            save=Mock(),
        )

        with patch("apps.esocial.admin.evento.messages.add_message") as mocked_message:
            self.admin_obj.atualizar_identidade(SimpleNamespace(), [permitido, bloqueado])

        self.assertEqual(permitido.identidade, "NEW")
        permitido.save.assert_called_once_with()
        bloqueado.make_identidade.assert_not_called()
        mocked_message.assert_called_once()

    def test_delete_model_apaga_permitidos_e_reporta_bloqueados(self):
        permitido = SimpleNamespace(status=STATUS_EVENTO_IMPORTADO, delete=Mock())
        bloqueado = SimpleNamespace(
            status=STATUS_EVENTO_ENVIADO,
            identidade="ID2",
            get_status_display=lambda: "Enviado",
        )

        with patch("apps.esocial.admin.evento.messages.add_message") as mocked_message:
            self.admin_obj.delete_model(SimpleNamespace(), [permitido, bloqueado])

        permitido.delete.assert_called_once_with()
        self.assertEqual(mocked_message.call_count, 2)
        self.assertIn("1 eventos apagados", mocked_message.call_args_list[-1][0][2])

    def test_validar_chama_vinculo_quando_sem_lote(self):
        sem_lote = SimpleNamespace(
            status=STATUS_EVENTO_IMPORTADO,
            lote=None,
            vincular_transmissor=Mock(),
            validar=Mock(),
        )
        com_lote = SimpleNamespace(
            status=STATUS_EVENTO_CADASTRADO,
            lote=object(),
            vincular_transmissor=Mock(),
            validar=Mock(),
        )
        ignorado = SimpleNamespace(
            status=999,
            lote=None,
            vincular_transmissor=Mock(),
            validar=Mock(),
        )

        with patch("apps.esocial.admin.evento.messages.add_message") as mocked_message:
            self.admin_obj.validar(SimpleNamespace(), [sem_lote, com_lote, ignorado])

        sem_lote.vincular_transmissor.assert_called_once_with()
        sem_lote.validar.assert_called_once_with()
        com_lote.vincular_transmissor.assert_not_called()
        com_lote.validar.assert_called_once_with()
        ignorado.validar.assert_not_called()
        self.assertIn("2 eventos validados", mocked_message.call_args[0][2])

    def test_abrir_evento_edicao_chama_metodo_para_todos(self):
        o1 = SimpleNamespace(abrir_evento_para_edicao=Mock())
        o2 = SimpleNamespace(abrir_evento_para_edicao=Mock())

        self.admin_obj.abrir_evento_edicao(SimpleNamespace(), [o1, o2])

        o1.abrir_evento_para_edicao.assert_called_once()
        o2.abrir_evento_para_edicao.assert_called_once()

    def test_has_delete_permission_retorna_false(self):
        self.assertFalse(self.admin_obj.has_delete_permission(SimpleNamespace()))

    def test_response_change_atualizar_identidade(self):
        request = SimpleNamespace(POST={"_atualizar_identidade": "1"})
        obj = SimpleNamespace(
            make_identidade=Mock(return_value="IDN"),
            save=Mock(),
            identidade="OLD",
        )
        self.admin_obj.message_user = Mock()

        response = self.admin_obj.response_change(request, obj)

        self.assertIsInstance(response, HttpResponseRedirect)
        obj.make_identidade.assert_called_once_with(request=request)
        obj.save.assert_called_once_with()
        self.admin_obj.message_user.assert_called_once()

    def test_response_change_duplicar_evento(self):
        request = SimpleNamespace(POST={"_duplicar_evento": "1"})
        obj = SimpleNamespace(duplicar_evento=Mock(return_value=SimpleNamespace(identidade="NOVO")))
        self.admin_obj.message_user = Mock()

        response = self.admin_obj.response_change(request, obj)

        self.assertIsInstance(response, HttpResponseRedirect)
        obj.duplicar_evento.assert_called_once_with(request=request)
        self.admin_obj.message_user.assert_called_once()

    def test_response_change_apagar_permitido(self):
        request = SimpleNamespace(POST={"_apagar": "1"})
        obj = SimpleNamespace(status=STATUS_EVENTO_CADASTRADO, delete=Mock())

        response = self.admin_obj.response_change(request, obj)

        self.assertIsInstance(response, HttpResponseRedirect)
        obj.delete.assert_called_once_with()

    def test_response_change_apagar_nao_permitido_retorna_super(self):
        request = SimpleNamespace(POST={"_apagar": "1"})
        obj = SimpleNamespace(
            status=STATUS_EVENTO_ENVIADO,
            identidade="ID3",
            get_status_display=lambda: "Enviado",
        )

        with patch("apps.esocial.admin.evento.messages.add_message") as mocked_message, patch(
            "django.contrib.admin.options.ModelAdmin.response_change",
            return_value="fallback",
        ):
            response = self.admin_obj.response_change(request, obj)

        self.assertEqual(response, "fallback")
        mocked_message.assert_called_once()

    def test_response_change_enviar_trata_error_warning_e_sucesso(self):
        cenarios = [
            ("error", "error"),
            ("warning", "warning"),
            ("ok", "message_user"),
        ]

        for retorno, esperado in cenarios:
            with self.subTest(retorno=retorno):
                request = SimpleNamespace(POST={"_enviar": "1"})
                obj = SimpleNamespace(
                    enviar=Mock(return_value={"retorno": retorno, "mensagem": "M"})
                )
                self.admin_obj.message_user = Mock()

                with patch("apps.esocial.admin.evento.messages.error") as mocked_error, patch(
                    "apps.esocial.admin.evento.messages.warning"
                ) as mocked_warning:
                    response = self.admin_obj.response_change(request, obj)

                self.assertIsInstance(response, HttpResponseRedirect)
                if esperado == "error":
                    mocked_error.assert_called_once()
                    mocked_warning.assert_not_called()
                    self.admin_obj.message_user.assert_not_called()
                elif esperado == "warning":
                    mocked_warning.assert_called_once()
                    mocked_error.assert_not_called()
                    self.admin_obj.message_user.assert_not_called()
                else:
                    self.admin_obj.message_user.assert_called_once()
                    mocked_error.assert_not_called()
                    mocked_warning.assert_not_called()

    def test_response_change_consultar_trata_error_warning_e_sucesso(self):
        cenarios = [
            ("error", "error"),
            ("warning", "warning"),
            ("ok", "message_user"),
        ]

        for retorno, esperado in cenarios:
            with self.subTest(retorno=retorno):
                request = SimpleNamespace(POST={"_consultar": "1"})
                obj = SimpleNamespace(
                    lote=SimpleNamespace(
                        consultar=Mock(return_value={"retorno": retorno, "mensagem": "M"})
                    )
                )
                self.admin_obj.message_user = Mock()

                with patch("apps.esocial.admin.evento.messages.error") as mocked_error, patch(
                    "apps.esocial.admin.evento.messages.warning"
                ) as mocked_warning:
                    response = self.admin_obj.response_change(request, obj)

                self.assertIsInstance(response, HttpResponseRedirect)
                if esperado == "error":
                    mocked_error.assert_called_once()
                    mocked_warning.assert_not_called()
                    self.admin_obj.message_user.assert_not_called()
                elif esperado == "warning":
                    mocked_warning.assert_called_once()
                    mocked_error.assert_not_called()
                    self.admin_obj.message_user.assert_not_called()
                else:
                    self.admin_obj.message_user.assert_called_once()
                    mocked_error.assert_not_called()
                    mocked_warning.assert_not_called()

    def test_response_change_abrir_evento_para_edicao(self):
        request = SimpleNamespace(POST={"_abrir_evento_para_edicao": "1"})
        obj = SimpleNamespace(abrir_evento_para_edicao=Mock())

        response = self.admin_obj.response_change(request, obj)

        self.assertIsInstance(response, HttpResponseRedirect)
        obj.abrir_evento_para_edicao.assert_called_once_with(request=request)

    def test_response_change_validar_com_e_sem_lote(self):
        sem_lote = SimpleNamespace(
            lote=None,
            vincular_transmissor=Mock(),
            validar=Mock(),
        )
        com_lote = SimpleNamespace(
            lote=object(),
            vincular_transmissor=Mock(),
            validar=Mock(),
        )
        request = SimpleNamespace(POST={"_validar": "1"})

        response1 = self.admin_obj.response_change(request, sem_lote)
        response2 = self.admin_obj.response_change(request, com_lote)

        self.assertIsInstance(response1, HttpResponseRedirect)
        self.assertIsInstance(response2, HttpResponseRedirect)
        sem_lote.vincular_transmissor.assert_called_once_with(request=request)
        sem_lote.validar.assert_called_once_with(request=request)
        com_lote.vincular_transmissor.assert_not_called()
        com_lote.validar.assert_called_once_with(request=request)

    def test_response_change_sem_acao_delega_para_super(self):
        request = SimpleNamespace(POST={})
        obj = SimpleNamespace()

        with patch(
            "django.contrib.admin.options.ModelAdmin.response_change",
            return_value="super-response",
        ) as mocked_super:
            response = self.admin_obj.response_change(request, obj)

        self.assertEqual(response, "super-response")
        mocked_super.assert_called_once_with(request, obj)

    def test_get_queryset_superuser_retorna_queryset_original(self):
        queryset = _FakeQuerySet()
        request = SimpleNamespace(user=SimpleNamespace(is_superuser=True, eventos=["s1000"]))

        with patch("django.contrib.admin.options.ModelAdmin.get_queryset", return_value=queryset):
            result = self.admin_obj.get_queryset(request)

        self.assertIs(result, queryset)

    def test_get_queryset_usuario_normal_filtra_por_eventos(self):
        queryset = _FakeQuerySet()
        request = SimpleNamespace(
            user=SimpleNamespace(is_superuser=False, eventos=["s1000", "s2200"])
        )

        with patch("django.contrib.admin.options.ModelAdmin.get_queryset", return_value=queryset):
            result = self.admin_obj.get_queryset(request)

        self.assertIs(result, queryset)
        self.assertEqual(queryset.filtered_kwargs, {"evento__in": ["s1000", "s2200"]})

    def test_get_form_define_usuario_atual(self):
        request = SimpleNamespace(user=SimpleNamespace(id=1))
        fake_form = type("FakeForm", (), {})

        with patch("django.contrib.admin.options.ModelAdmin.get_form", return_value=fake_form):
            result = self.admin_obj.get_form(request)

        self.assertIs(result, fake_form)
        self.assertIs(result.current_user, request.user)
