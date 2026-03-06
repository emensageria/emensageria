from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from apps.esocial.choices import (
    EVENTO_ORIGEM_API,
    EVENTO_ORIGEM_SISTEMA,
    STATUS_EVENTO_AGUARD_ENVIO,
    STATUS_EVENTO_CADASTRADO,
    STATUS_EVENTO_ENVIADO,
    STATUS_EVENTO_ERRO,
    STATUS_EVENTO_IMPORTADO,
)
from apps.esocial.models import Certificados, Lotes, Transmissor
from apps.esocial.models.evento import Eventos


class _FakeAllQuery:

    def __init__(self, all_result):
        self._all_result = all_result

    def all(self):
        return self._all_result


class _FakeFilterAndAll:

    def __init__(self, all_result):
        self._all_result = all_result

    def filter(self, **_kwargs):
        return self

    def all(self):
        return self._all_result


class _FakeHistorico:

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def save(self):
        return None


class EventosModelTests(SimpleTestCase):

    @staticmethod
    def _certificado():
        return Certificados(nome="Certificado")

    @classmethod
    def _transmissor(cls, cert=None):
        certificado = cert or cls._certificado()
        return Transmissor(
            transmissor_tpinsc=1,
            transmissor_nrinsc="12345678000199",
            nome_empresa="Empresa X",
            tpinsc=1,
            nrinsc="12345678",
            certificado=certificado,
        )

    @classmethod
    def _lote(cls, transmissor=None):
        trans = transmissor or cls._transmissor()
        return Lotes(
            transmissor=trans,
            empregador_tpinsc=1,
            empregador_nrinsc="12345678",
            grupo=1,
            status=0,
        )

    @staticmethod
    def _evento(**kwargs):
        evento = Eventos(
            versao="v_S_01_03_00",
            evento="s1000",
            tpinsc=1,
            nrinsc="12345678",
            status=STATUS_EVENTO_CADASTRADO,
            origem=EVENTO_ORIGEM_SISTEMA,
            is_aberto=True,
        )
        evento.id = kwargs.pop("id", 1)
        evento.pk = kwargs.pop("pk", evento.id)
        evento.created_at = kwargs.pop("created_at", datetime(2024, 1, 2, 3, 4, 5))
        evento.identidade = kwargs.pop("identidade", "ID_INICIAL")
        evento.evento_xml = kwargs.pop("evento_xml", None)
        evento.evento_json = kwargs.pop("evento_json", None)
        evento.lote = kwargs.pop("lote", None)
        evento.certificado = kwargs.pop("certificado", None)
        evento.ocorrencias_json = kwargs.pop("ocorrencias_json", None)
        evento.retorno_envio_json = kwargs.pop("retorno_envio_json", None)
        evento.retorno_consulta_json = kwargs.pop("retorno_consulta_json", None)
        evento.retorno_envio_lote_json = kwargs.pop("retorno_envio_lote_json", None)
        evento.retorno_consulta_lote_json = kwargs.pop("retorno_consulta_lote_json", None)
        for key, value in kwargs.items():
            setattr(evento, key, value)
        return evento

    def test_is_editable_true_e_false(self):
        evento = self._evento()

        with patch("pathlib.Path.is_file", side_effect=[True, False]):
            self.assertTrue(evento.is_editable())
            self.assertFalse(evento.is_editable())

    def test_get_grupo_esocial_e_helpers_de_retorno(self):
        evento = self._evento(evento="s1000")
        self.assertEqual(evento.get_grupo_esocial(), 1)

        evento.evento = "s1200"
        self.assertEqual(evento.get_grupo_esocial(), 3)

        evento.evento = "s2200"
        self.assertEqual(evento.get_grupo_esocial(), 2)

        evento.retorno_envio_json = None
        evento.retorno_consulta_json = None
        evento.retorno_envio_lote_json = None
        evento.retorno_consulta_lote_json = None
        evento.ocorrencias_json = None

        self.assertEqual(evento.retorno_envio(), {})
        self.assertEqual(evento.retorno_consulta(), {})
        self.assertEqual(evento.retorno_envio_lote(), {})
        self.assertEqual(evento.retorno_consulta_lote(), {})
        self.assertEqual(evento.ocorrencias(), {})
        self.assertEqual(str(evento), evento.identidade)

    def test_replace_id_xsd_pdf_xml(self):
        evento = self._evento(identidade="ID123")
        xml = '<eSocial><evtInfoEmpregador Id="IDOLD"></evtInfoEmpregador></eSocial>'

        replaced = evento.replace_id(xml, "IDNOVO")

        self.assertIn('Id="IDNOVO"', replaced)
        self.assertIn("evtInfoEmpregador.xsd", evento.xsd_file())
        self.assertTrue(evento.pdf_file().endswith("ID123.pdf"))
        self.assertTrue(evento.xml_file().endswith("ID123.xml"))
        self.assertTrue(
            evento.xml_file("20240101000000").endswith("ID123_20240101000000.xml")
        )

    def test_make_identidade_com_loop_e_replace_no_xml(self):
        evento = self._evento(
            evento_xml='<eSocial><evtInfoEmpregador Id="IDOLD"></evtInfoEmpregador></eSocial>',
            identidade="IDOLD",
        )
        fake_exclude = _FakeFilterAndAll(all_result=[["dup"], []])
        fake_exclude.all = Mock(side_effect=[["dup"], []])

        with patch(
            "apps.esocial.models.evento.Eventos.objects.exclude",
            return_value=fake_exclude,
        ), patch.object(evento, "save", Mock()):
            identidade = evento.make_identidade()

        self.assertTrue(identidade.startswith("ID1"))
        self.assertIn(identidade, evento.evento_xml)

    def test_make_identidade_sem_evento_xml(self):
        evento = self._evento(evento_xml=None, identidade=None)
        fake_exclude = _FakeFilterAndAll(all_result=[])

        with patch(
            "apps.esocial.models.evento.Eventos.objects.exclude",
            return_value=fake_exclude,
        ), patch.object(evento, "save", Mock()):
            identidade = evento.make_identidade()

        self.assertTrue(identidade.startswith("ID1"))
        self.assertIsNone(evento.evento_xml)

    def test_vincular_transmissor_reaproveita_lote(self):
        evento = self._evento(lote=None)
        evento.save = Mock()

        transmissor = self._transmissor()
        lote_existente = self._lote(transmissor=transmissor)

        with patch(
            "apps.esocial.models.Transmissor.objects.filter",
            return_value=_FakeAllQuery([transmissor]),
        ), patch(
            "apps.esocial.models.Lotes.objects.filter",
            return_value=_FakeAllQuery([lote_existente]),
        ), patch(
            "apps.esocial.models.evento.Eventos.objects.filter",
            return_value=_FakeAllQuery([1, 2]),
        ):
            result = evento.vincular_transmissor()

        self.assertIs(result, lote_existente)
        self.assertIs(evento.lote, lote_existente)
        evento.save.assert_called_once_with()

    def test_vincular_transmissor_com_lote_existente_sai_sem_alterar(self):
        lote = self._lote()
        evento = self._evento(lote=lote)

        self.assertIsNone(evento.vincular_transmissor())

    def test_vincular_transmissor_com_lote_cheio_tenta_proximo(self):
        evento = self._evento(lote=None)
        evento.save = Mock()
        transmissor = self._transmissor()
        lote1 = self._lote(transmissor=transmissor)
        lote2 = self._lote(transmissor=transmissor)

        with patch(
            "apps.esocial.models.Transmissor.objects.filter",
            return_value=_FakeAllQuery([transmissor]),
        ), patch(
            "apps.esocial.models.Lotes.objects.filter",
            return_value=_FakeAllQuery([lote1, lote2]),
        ), patch(
            "apps.esocial.models.evento.Eventos.objects.filter",
            side_effect=[_FakeAllQuery([1]), _FakeAllQuery([])],
        ), patch("apps.esocial.models.evento.settings.ESOCIAL_LOTE_MAX", 1):
            result = evento.vincular_transmissor()

        self.assertIs(result, lote2)

    def test_vincular_transmissor_cria_lote_quando_necessario(self):
        evento = self._evento(lote=None)
        evento.save = Mock()

        transmissor = self._transmissor()
        with patch(
            "apps.esocial.models.Transmissor.objects.filter",
            return_value=_FakeAllQuery([transmissor]),
        ), patch(
            "apps.esocial.models.Lotes.objects.filter",
            return_value=_FakeAllQuery([]),
        ), patch("apps.esocial.models.Lotes.save"):
            result = evento.vincular_transmissor()

        self.assertIsInstance(result, Lotes)
        self.assertIs(evento.lote, result)

    def test_vincular_transmissor_sem_transmissor_com_request(self):
        evento = self._evento(lote=None)
        with patch(
            "apps.esocial.models.Transmissor.objects.filter",
            return_value=_FakeAllQuery([]),
        ), patch(
            "apps.esocial.models.evento.messages.error"
        ) as mocked_error:
            evento.vincular_transmissor(request=SimpleNamespace())

        mocked_error.assert_called_once()

    def test_vincular_transmissor_sem_transmissor_sem_request(self):
        evento = self._evento(lote=None)
        with patch(
            "apps.esocial.models.Transmissor.objects.filter",
            return_value=_FakeAllQuery([]),
        ), patch("apps.esocial.models.evento.messages.error") as mocked_error:
            evento.vincular_transmissor()

        mocked_error.assert_not_called()

    def test_enviar_retorna_lote_existente_ou_cria_novo(self):
        transmissor = self._transmissor()
        lote = self._lote(transmissor=transmissor)
        lote.enviar = Mock(return_value={"a": 1})
        evento = self._evento(
            lote=lote
        )

        with patch(
            "apps.esocial.models.Transmissor.objects.get",
            return_value=transmissor,
        ):
            result = evento.enviar()

        self.assertEqual(result, {"a": 1})

        evento2 = self._evento(lote=None)
        evento2.save = Mock()
        with patch(
            "apps.esocial.models.Transmissor.objects.get",
            return_value=transmissor,
        ), patch("apps.esocial.models.Lotes.save"), patch(
            "apps.esocial.models.Lotes.enviar",
            return_value={"retorno": "ok"},
        ):
            result2 = evento2.enviar()

        self.assertEqual(result2, {"retorno": "ok"})
        evento2.save.assert_called_once_with()

    def test_consultar_e_salvar_certificado_transmissor(self):
        lote = self._lote()
        lote.consultar = Mock(return_value={"k": 1})
        evento = self._evento(lote=lote)
        self.assertEqual(evento.consultar(), {"k": 1})

        evento.lote = None
        self.assertEqual(evento.consultar(), {})

        cert = self._certificado()
        trans = self._transmissor(cert=cert)
        evento2 = self._evento(lote=self._lote(transmissor=trans), certificado=None)
        evento2.save = Mock()
        evento2.salvar_certificado_transmissor()
        self.assertIs(evento2.certificado, cert)
        evento2.save.assert_called_once_with()

    def test_salvar_certificado_transmissor_sem_lote_nao_faz_nada(self):
        evento = self._evento(lote=None, certificado=None)
        evento.save = Mock()

        evento.salvar_certificado_transmissor()

        evento.save.assert_not_called()

    def test_assinar_fluxo_sucesso(self):
        evento = self._evento(evento_xml="<eSocial/>", lote=None, certificado=None)
        fake_cert = self._certificado()
        fake_cert.certificado = SimpleNamespace(file=SimpleNamespace(name="/tmp/cert.pfx"))
        fake_cert.get_senha = Mock(return_value="123")
        fake_lote = self._lote(transmissor=self._transmissor(cert=fake_cert))

        def _vincular():
            evento.lote = fake_lote

        def _salvar_certificado():
            evento.certificado = fake_cert

        evento.vincular_transmissor = Mock(side_effect=_vincular)
        evento.salvar_certificado_transmissor = Mock(side_effect=_salvar_certificado)
        evento.save = Mock()
        evento.xml_file = Mock(side_effect=["/tmp/a.xml", "/tmp/b.xml"])

        with patch(
            "apps.esocial.models.evento.esocial.utils.pkcs12_data",
            return_value="cert",
        ), patch(
            "apps.esocial.models.evento.load_fromstring", return_value="xml"
        ), patch("apps.esocial.models.evento.sign", return_value="signed"), patch(
            "apps.esocial.models.evento.etree.tostring", return_value=b"<signed/>"
        ), patch("apps.esocial.models.evento.save_file") as mocked_save_file:
            evento.assinar()

        evento.vincular_transmissor.assert_called_once_with()
        evento.salvar_certificado_transmissor.assert_called_once_with()
        evento.save.assert_called_once_with()
        self.assertEqual(evento.evento_xml, "<signed/>")
        self.assertEqual(mocked_save_file.call_count, 2)

    def test_assinar_quando_lote_ja_existe_nao_vincula(self):
        evento = self._evento(evento_xml="<eSocial/>", lote=self._lote(), certificado=None)
        evento.vincular_transmissor = Mock()
        evento.salvar_certificado_transmissor = Mock()

        evento.assinar()

        evento.vincular_transmissor.assert_not_called()
        evento.salvar_certificado_transmissor.assert_called_once_with()

    def test_assinar_fluxo_erro_com_request(self):
        evento = self._evento(evento_xml="<eSocial/>", lote=None, certificado=None)
        evento.vincular_transmissor = Mock(return_value=None)

        with patch("apps.esocial.models.evento.messages.error") as mocked_error:
            result = evento.assinar(request=SimpleNamespace())

        self.assertIsNone(result)
        mocked_error.assert_called_once()

    def test_assinar_fluxo_erro_sem_request(self):
        evento = self._evento(evento_xml="<eSocial/>", lote=None, certificado=None)
        evento.vincular_transmissor = Mock(return_value=None)

        with patch("apps.esocial.models.evento.messages.error") as mocked_error:
            result = evento.assinar()

        self.assertIsNone(result)
        mocked_error.assert_not_called()

    def test_create_xml_partindo_de_evento_xml(self):
        evento = self._evento(
            origem=EVENTO_ORIGEM_API,
            status=STATUS_EVENTO_IMPORTADO,
            identidade=None,
            evento_xml="<evtInfoEmpregador><ideEmpregador/></evtInfoEmpregador>",
        )
        evento.save = Mock()
        evento.make_identidade = Mock(
            side_effect=lambda: setattr(evento, "identidade", "IDGERADO")
        )
        evento.assinar = Mock()
        evento.xml_file = Mock(side_effect=["/tmp/a.xml", "/tmp/b.xml"])
        fake_filter = SimpleNamespace(update=Mock())

        with patch(
            "apps.esocial.models.evento.Eventos.objects.filter",
            return_value=fake_filter,
        ), patch(
            "apps.esocial.models.evento.save_file"
        ) as mocked_save_file:
            evento.create_xml()

        evento.make_identidade.assert_called_once_with()
        self.assertIn("xmlns", evento.evento_xml)
        fake_filter.update.assert_called_once()
        self.assertEqual(mocked_save_file.call_count, 2)
        evento.assinar.assert_called_once_with(None)

    def test_create_xml_partindo_de_evento_xml_sem_mudancas(self):
        evento = self._evento(
            origem=EVENTO_ORIGEM_API,
            status=STATUS_EVENTO_IMPORTADO,
            identidade="IDEXISTE",
            evento_xml=(
                "<eSocial xmlns=\"http://www.esocial.gov.br/schema/evt/evtInfoEmpregador/"
                "v_S_01_03_00\"><evtInfoEmpregador Id=\"IDEXISTE\"/></eSocial>"
            ),
        )
        evento.save = Mock()
        evento.assinar = Mock()
        evento.xml_file = Mock(side_effect=["/tmp/a.xml", "/tmp/b.xml"])
        fake_filter = SimpleNamespace(update=Mock())

        with patch(
            "apps.esocial.models.evento.Eventos.objects.filter",
            return_value=fake_filter,
        ), patch("apps.esocial.models.evento.save_file"):
            evento.create_xml()

        evento.assinar.assert_called_once_with(None)

    def test_create_xml_partindo_de_evento_xml_com_wildcard_e_signature(self):
        evento = self._evento(
            origem=EVENTO_ORIGEM_API,
            status=STATUS_EVENTO_IMPORTADO,
            identidade="IDJA",
            evento_xml="<eSocial xmlns=\"http://x\"><evtInfoEmpregador/><Signature/></eSocial>",
        )
        evento.save = Mock()
        evento.assinar = Mock()
        evento.xml_file = Mock(side_effect=["/tmp/a.xml", "/tmp/b.xml"])
        fake_filter = SimpleNamespace(update=Mock())

        with patch(
            "apps.esocial.models.evento.Eventos.objects.filter",
            return_value=fake_filter,
        ), patch(
            "apps.esocial.models.evento.save_file"
        ):
            evento.create_xml()

        evento.assinar.assert_not_called()

    def test_create_xml_partindo_de_evento_xml_sem_tag_gera_erro(self):
        evento = self._evento(
            origem=EVENTO_ORIGEM_API,
            status=STATUS_EVENTO_IMPORTADO,
            identidade="IDX",
            evento_xml="<eSocial><outraTag/></eSocial>",
        )
        evento.save = Mock()

        with self.assertRaises(ValueError):
            evento.create_xml()

    def test_create_xml_partindo_de_evento_json(self):
        evento = self._evento(
            origem=EVENTO_ORIGEM_API,
            status=STATUS_EVENTO_IMPORTADO,
            identidade="IDJSON",
            evento_xml=None,
            evento_json={"evtInfoEmpregador": {"dt": "01/02/2024", "vazio": ""}},
        )
        evento.save = Mock()
        evento.assinar = Mock(return_value=None)
        evento.xml_file = Mock(side_effect=["/tmp/a.xml", "/tmp/b.xml"])
        fake_filter = SimpleNamespace(update=Mock())

        with patch(
            "apps.esocial.models.evento.Eventos.objects.filter",
            return_value=fake_filter,
        ), patch(
            "apps.esocial.models.evento.save_file"
        ), patch(
            "dicttoxml.dicttoxml",
            return_value=(
                b"<eSocial><evtInfoEmpregador><dt>01/02/2024</dt>"
                b"<vazio></vazio></evtInfoEmpregador></eSocial>"
            ),
        ):
            evento.create_xml()

        self.assertIn("2024-02-01", evento.evento_xml)
        evento.assinar.assert_called_once_with(None)

    def test_create_xml_partindo_de_evento_json_sem_identidade_e_container_redundante(self):
        evento = self._evento(
            origem=EVENTO_ORIGEM_API,
            status=STATUS_EVENTO_IMPORTADO,
            identidade=None,
            evento_xml=None,
            evento_json={"dummy": "x"},
        )
        evento.save = Mock()
        evento.assinar = Mock(return_value=None)
        evento.xml_file = Mock(side_effect=["/tmp/a.xml", "/tmp/b.xml"])
        fake_filter = SimpleNamespace(update=Mock())

        with patch(
            "apps.esocial.models.evento.Eventos.objects.filter",
            return_value=fake_filter,
        ), patch("apps.esocial.models.evento.save_file"), patch(
            "dicttoxml.dicttoxml",
            return_value=(
                b"<eSocial><dup><dup><x>1</x></dup><dup><x>2</x></dup></dup>"
                b"<evtInfoEmpregador><campo>ok</campo></evtInfoEmpregador></eSocial>"
            ),
        ):
            evento.create_xml()

        self.assertIn("<dup><x>1</x></dup><dup><x>2</x></dup>", evento.evento_xml)

    def test_create_xml_partindo_de_status_cadastrado_editavel(self):
        evento = self._evento(
            origem=EVENTO_ORIGEM_SISTEMA,
            status=STATUS_EVENTO_CADASTRADO,
            identidade="IDCAD",
            evento_xml=None,
            evento_json={"evtInfoEmpregador": {"campo": "ok"}},
        )
        evento.save = Mock()
        evento.assinar = Mock(return_value=None)
        evento.xml_file = Mock(side_effect=["/tmp/a.xml", "/tmp/b.xml"])

        with patch.object(evento, "is_editable", return_value=True), patch(
            "apps.esocial.models.evento.Eventos.objects.filter",
            return_value=SimpleNamespace(update=Mock()),
        ), patch("apps.esocial.models.evento.save_file"), patch(
            "dicttoxml.dicttoxml",
            return_value=(
                b"<eSocial><evtInfoEmpregador><campo>ok</campo>"
                b"</evtInfoEmpregador></eSocial>"
            ),
        ):
            evento.create_xml()

        evento.assinar.assert_called_once_with(None)

    def test_create_xml_sem_condicoes_nao_faz_nada(self):
        evento = self._evento(
            origem=EVENTO_ORIGEM_SISTEMA,
            status=STATUS_EVENTO_ENVIADO,
            evento_xml=None,
            evento_json=None,
        )

        evento.create_xml()

    def test_validar_com_schema_erro_sucesso_e_sem_schema(self):
        evento = self._evento(lote=self._lote())
        evento.create_xml = Mock()
        evento.save = Mock()

        erro = SimpleNamespace(reason="Falha", path="/x")
        with patch("apps.esocial.models.evento.VALIDAR_SCHEMA", True), patch(
            "config.functions.validar_schema", return_value=[erro]
        ), patch("apps.esocial.models.evento.messages.error") as mocked_error:
            evento.validar(request=SimpleNamespace())

        self.assertEqual(evento.status, STATUS_EVENTO_ERRO)
        self.assertIsNone(evento.lote)
        mocked_error.assert_called_once()

        evento2 = self._evento()
        evento2.create_xml = Mock()
        evento2.save = Mock()
        with patch("apps.esocial.models.evento.VALIDAR_SCHEMA", True), patch(
            "config.functions.validar_schema", return_value=[]
        ), patch("apps.esocial.models.evento.messages.success") as mocked_success:
            evento2.validar(request=SimpleNamespace())

        self.assertEqual(evento2.status, STATUS_EVENTO_AGUARD_ENVIO)
        mocked_success.assert_called_once()

        evento3 = self._evento()
        evento3.create_xml = Mock()
        evento3.save = Mock()
        with patch("apps.esocial.models.evento.VALIDAR_SCHEMA", False), patch(
            "apps.esocial.models.evento.messages.success"
        ) as mocked_success2:
            evento3.validar(request=SimpleNamespace())

        self.assertEqual(evento3.status, STATUS_EVENTO_AGUARD_ENVIO)
        mocked_success2.assert_called_once()

    def test_validar_sem_request_cobre_branches_de_saida(self):
        erro = SimpleNamespace(reason="Falha", path="/x")

        evento = self._evento(lote=self._lote())
        evento.create_xml = Mock()
        evento.save = Mock()
        with patch("apps.esocial.models.evento.VALIDAR_SCHEMA", True), patch(
            "config.functions.validar_schema", return_value=[erro]
        ), patch("apps.esocial.models.evento.messages.error") as mocked_error:
            evento.validar(request=None)
        mocked_error.assert_not_called()

        evento2 = self._evento()
        evento2.create_xml = Mock()
        evento2.save = Mock()
        with patch("apps.esocial.models.evento.VALIDAR_SCHEMA", True), patch(
            "config.functions.validar_schema", return_value=[]
        ), patch("apps.esocial.models.evento.messages.success") as mocked_success:
            evento2.validar(request=None)
        mocked_success.assert_not_called()

        evento3 = self._evento()
        evento3.create_xml = Mock()
        evento3.save = Mock()
        with patch("apps.esocial.models.evento.VALIDAR_SCHEMA", False), patch(
            "apps.esocial.models.evento.messages.success"
        ) as mocked_success2:
            evento3.validar(request=None)
        mocked_success2.assert_not_called()

    def test_duplicar_abrir_edicao_lista_e_fluxos(self):
        evento = self._evento(status=STATUS_EVENTO_IMPORTADO)
        evento.save = Mock()

        duplicated = evento.duplicar_evento()

        self.assertIs(duplicated, evento)
        self.assertEqual(evento.status, STATUS_EVENTO_CADASTRADO)
        self.assertIsNone(evento.lote)
        self.assertIsNone(evento.id)

        status_list = evento.abrir_evento_para_edicao_lista()
        self.assertIn(STATUS_EVENTO_IMPORTADO, status_list)

        evento.status = STATUS_EVENTO_IMPORTADO
        with patch("apps.esocial.models.evento.messages.success") as mocked_success:
            evento.abrir_evento_para_edicao(request=SimpleNamespace())

        self.assertTrue(evento.is_aberto)
        self.assertEqual(evento.status, STATUS_EVENTO_CADASTRADO)
        mocked_success.assert_called_once()

        evento2 = self._evento(status=999)
        with patch("apps.esocial.models.evento.messages.error") as mocked_error:
            evento2.abrir_evento_para_edicao(request=SimpleNamespace())

        mocked_error.assert_called_once()

    def test_abrir_evento_para_edicao_outros_ramos_sem_request(self):
        evento = self._evento(status=STATUS_EVENTO_ERRO)
        evento.save = Mock()

        evento.abrir_evento_para_edicao(request=None)
        self.assertEqual(evento.status, STATUS_EVENTO_ERRO)

        evento2 = self._evento(status=999)
        with patch("apps.esocial.models.evento.messages.error") as mocked_error:
            evento2.abrir_evento_para_edicao(request=None)

        mocked_error.assert_not_called()

    def test_save_custom_cria_historico_com_e_sem_identidade(self):
        evento = self._evento(identidade=None, id=31, pk=31)
        evento.make_identidade = Mock(
            side_effect=lambda: setattr(evento, "identidade", "ID31")
        )

        with patch("django.db.models.Model.save") as mocked_super, patch(
            "apps.esocial.models.evento.Eventos.objects.get",
            return_value=SimpleNamespace(),
        ), patch(
            "apps.esocial.models.evento.model_to_dict",
            return_value={
                "id": 31,
                "created_by": 7,
                "certificado": 9,
                "lote": 11,
                "evento": "s1000",
            },
        ), patch("apps.esocial.models.EventosHistorico", _FakeHistorico):
            evento.save()

        mocked_super.assert_called_once_with(
            force_insert=False,
            force_update=False,
            using=None,
            update_fields=None,
        )
        evento.make_identidade.assert_called_once_with()

        evento2 = self._evento(identidade="IDX", id=32, pk=32)
        evento2.make_identidade = Mock()
        with patch("django.db.models.Model.save"), patch(
            "apps.esocial.models.evento.Eventos.objects.get",
            return_value=SimpleNamespace(),
        ), patch(
            "apps.esocial.models.evento.model_to_dict",
            return_value={
                "id": 32,
                "created_by": None,
                "certificado": None,
                "lote": None,
                "evento": "s1000",
            },
        ), patch("apps.esocial.models.EventosHistorico", _FakeHistorico):
            evento2.save()

        evento2.make_identidade.assert_not_called()
