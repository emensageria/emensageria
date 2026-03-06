from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.admin.sites import AdminSite
from django.test import SimpleTestCase

from apps.esocial.admin.lote import EventosInline, LotesAdmin
from apps.esocial.choices import STATUS_TRANSMISSOR_AGUARDANDO
from apps.esocial.models import Eventos, Lotes


class LoteAdminTests(SimpleTestCase):

    def setUp(self):
        self.admin_obj = LotesAdmin(Lotes, AdminSite())
        self.inline_obj = EventosInline(Lotes, AdminSite())

    def test_eventos_inline_nao_permite_add_nem_change(self):
        request = SimpleNamespace(user=SimpleNamespace())

        self.assertFalse(self.inline_obj.has_add_permission(request))
        self.assertFalse(self.inline_obj.has_change_permission(request))

    def test_autorizar_envio_define_status_e_salva(self):
        obj = SimpleNamespace(status=0, save=Mock())

        self.admin_obj.autorizar_envio(request=SimpleNamespace(), queryset=[obj])

        self.assertEqual(obj.status, STATUS_TRANSMISSOR_AGUARDANDO)
        obj.save.assert_called_once_with()

    def test_enviar_lote_exibe_mensagem_com_id_e_retorno(self):
        obj = SimpleNamespace(
            id=10,
            enviar=Mock(return_value={"retorno": "ok", "mensagem": "enviado"}),
        )

        with patch("apps.esocial.admin.lote.messages.add_message") as mocked_message:
            self.admin_obj.enviar_lote(request=SimpleNamespace(), queryset=[obj])

        mocked_message.assert_called_once()
        mensagem = mocked_message.call_args[0][2]
        self.assertIn("10", mensagem)
        self.assertIn("ok", mensagem)
        self.assertIn("enviado", mensagem)

    def test_consultar_lote_exibe_mensagem_com_id_e_retorno(self):
        obj = SimpleNamespace(
            id=11,
            consultar=Mock(return_value={"retorno": "warning", "mensagem": "aguarde"}),
        )

        with patch("apps.esocial.admin.lote.messages.add_message") as mocked_message:
            self.admin_obj.consultar_lote(request=SimpleNamespace(), queryset=[obj])

        mocked_message.assert_called_once()
        mensagem = mocked_message.call_args[0][2]
        self.assertIn("11", mensagem)
        self.assertIn("warning", mensagem)
        self.assertIn("aguarde", mensagem)

    def test_lotes_admin_nao_permite_add_nem_change(self):
        request = SimpleNamespace(user=SimpleNamespace())

        self.assertFalse(self.admin_obj.has_add_permission(request))
        self.assertFalse(self.admin_obj.has_change_permission(request))

    def test_eventos_inline_usa_model_eventos(self):
        self.assertIs(EventosInline.model, Eventos)
