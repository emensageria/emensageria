import math
import sys
from datetime import datetime
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from apps.esocial.models.certificado import Certificados
from apps.esocial.models.lote import (
    CODIGOS_RESPOSTA_PROCESSADOS,
    CODIGO_AGUARDANDO_PROCESSAMENTO,
    ESOCIAL_LOTE_MAX,
    ESOCIAL_LOTE_MIN,
    Lotes,
    STATUS_EVENTO_ERRO,
    STATUS_EVENTO_PROCESSADO,
    STATUS_TRANSMISSOR_CADASTRADO,
    STATUS_TRANSMISSOR_ENVIADO,
    STATUS_TRANSMISSOR_ERRO_CONSULTA,
    STATUS_TRANSMISSOR_ERRO_ENVIO,
)
from apps.esocial.models.transmissor import Transmissor


class LotesModelTests(SimpleTestCase):

    def _build_lote(self):
        certificado = Certificados(nome="Certificado Teste")
        certificado.cert_host = MagicMock(return_value="cert.pfx")
        certificado.get_senha = MagicMock(return_value="123")
        transmissor = Transmissor(
            transmissor_tpinsc=1,
            transmissor_nrinsc="123",
            nome_empresa="Empresa Teste",
            tpinsc=1,
            nrinsc="12345678",
            certificado=certificado,
        )
        lote = Lotes(
            id=10,
            transmissor=transmissor,
            empregador_tpinsc=1,
            empregador_nrinsc="12.345.678/0001-99",
            grupo=1,
            status=STATUS_TRANSMISSOR_CADASTRADO,
            protocolo="PROTOCOLO-1",
        )
        lote.save = MagicMock()
        return lote

    def test_save_remove_nao_numericos_em_empregador_nrinsc(self):
        lote = self._build_lote()

        with patch("django.db.models.base.Model.save", return_value=None) as save_mock:
            Lotes.save(lote)

        self.assertEqual(lote.empregador_nrinsc, "12345678000199")
        save_mock.assert_called_once()

    def test_quant_eventos_consulta_queryset_e_count(self):
        lote = self._build_lote()
        queryset = MagicMock()
        queryset.count.return_value = 7

        with patch("apps.esocial.models.evento.Eventos.objects.filter", return_value=queryset):
            self.assertEqual(lote.quant_eventos(), 7)

    def test_eventos_concatena_xml_dos_eventos(self):
        lote = self._build_lote()
        evento_1 = SimpleNamespace(identidade="ID1", xml_file=MagicMock(return_value="a.xml"))
        evento_2 = SimpleNamespace(identidade="ID2", xml_file=MagicMock(return_value="b.xml"))
        queryset = MagicMock()
        queryset.all.return_value = [evento_1, evento_2]

        with patch("apps.esocial.models.evento.Eventos.objects.filter", return_value=queryset), \
                patch("apps.esocial.models.lote.read_file", side_effect=["<a/>", "<b/>"]):
            xml = lote.eventos()

        self.assertIn('<evento Id="ID1"><a/></evento>', xml)
        self.assertIn('<evento Id="ID2"><b/></evento>', xml)

    def test_get_eventos_retorna_queryset_all(self):
        lote = self._build_lote()
        queryset = MagicMock()
        queryset.all.return_value = ["evt1", "evt2"]

        with patch("apps.esocial.models.evento.Eventos.objects.filter", return_value=queryset):
            self.assertEqual(lote.get_eventos(), ["evt1", "evt2"])

    def test_get_request_e_get_response_criam_caminhos(self):
        lote = self._build_lote()
        fixed_dt = datetime(2024, 1, 2, 3, 4, 5)

        with patch("apps.esocial.models.lote.datetime") as dt_mock, \
                patch("apps.esocial.models.lote.create_dir") as create_dir_mock:
            dt_mock.now.return_value = fixed_dt
            request_path = lote.get_request("WsEnviarLoteEventos", "IGNORADO")
            response_path = lote.get_response("WsEnviarLoteEventos", "IGNORADO")

        self.assertIn("request", request_path)
        self.assertIn("response", response_path)
        create_dir_mock.assert_any_call(request_path)
        create_dir_mock.assert_any_call(response_path)

    def test__enviar_monta_ws_client_envia_eventos_e_retorna_xmls(self):
        lote = self._build_lote()
        lote.get_eventos = MagicMock(return_value=[SimpleNamespace(evento_xml="<xml/>")])

        fake_esocial = ModuleType("esocial")
        fake_xml = ModuleType("esocial.xml")
        fake_client = ModuleType("esocial.client")

        ws_client = MagicMock()
        ws_client.send.return_value = ("RESULT_OBJ", "BATCH_OBJ")
        fake_client.WSClient = MagicMock(return_value=ws_client)
        fake_xml.load_fromstring = MagicMock(return_value="EVENTO_XML_OBJ")
        fake_xml.dump_tostring = MagicMock(side_effect=["RESULT_XML", "BATCH_XML"])
        fake_esocial.xml = fake_xml
        fake_esocial.client = fake_client

        with patch.dict(
            sys.modules,
            {"esocial": fake_esocial, "esocial.xml": fake_xml, "esocial.client": fake_client},
        ):
            result_xml, batch_xml = lote._enviar()

        self.assertEqual(result_xml, "RESULT_XML")
        self.assertEqual(batch_xml, "BATCH_XML")
        ws_client.add_event.assert_called_once_with("EVENTO_XML_OBJ")
        ws_client.send.assert_called_once_with(group_id=lote.grupo)

    def test_enviar_retorna_erro_quando_preencondicoes_nao_sao_atendidas(self):
        lote = self._build_lote()
        lote.status = 999
        lote.quant_eventos = MagicMock(return_value=1)

        response = lote.enviar(request=None)
        self.assertEqual(response["retorno"], "error")

    def test_enviar_precondicao_invalida_com_request_chama_message_error(self):
        lote = self._build_lote()
        lote.status = 999
        lote.quant_eventos = MagicMock(return_value=1)

        with patch("apps.esocial.models.lote.messages.error") as error_mock:
            response = lote.enviar(request=SimpleNamespace())

        self.assertEqual(response["retorno"], "error")
        error_mock.assert_called_once()

    def test_enviar_retorna_erro_para_lote_abaixo_do_minimo(self):
        lote = self._build_lote()
        lote.quant_eventos = MagicMock(return_value=ESOCIAL_LOTE_MIN - 0.5)

        response = lote.enviar(request=None)
        self.assertEqual(response["retorno"], "error")
        self.assertIn("inferior", response["mensagem"])

    def test_enviar_lote_abaixo_do_minimo_com_request_chama_message_error(self):
        lote = self._build_lote()
        lote.quant_eventos = MagicMock(return_value=ESOCIAL_LOTE_MIN - 0.5)

        with patch("apps.esocial.models.lote.messages.error") as error_mock:
            response = lote.enviar(request=SimpleNamespace())

        self.assertEqual(response["retorno"], "error")
        error_mock.assert_called_once()

    def test_enviar_retorna_erro_para_lote_acima_do_maximo(self):
        lote = self._build_lote()
        lote.quant_eventos = MagicMock(return_value=ESOCIAL_LOTE_MAX + 1)

        response = lote.enviar(request=None)
        self.assertEqual(response["retorno"], "error")
        self.assertIn("superior", response["mensagem"])

    def test_enviar_lote_acima_do_maximo_com_request_chama_message_error(self):
        lote = self._build_lote()
        lote.quant_eventos = MagicMock(return_value=ESOCIAL_LOTE_MAX + 1)

        with patch("apps.esocial.models.lote.messages.error") as error_mock:
            response = lote.enviar(request=SimpleNamespace())

        self.assertEqual(response["retorno"], "error")
        error_mock.assert_called_once()

    def test_enviar_retorna_erro_generico_no_caminho_else(self):
        lote = self._build_lote()
        lote.quant_eventos = MagicMock(return_value=math.nan)

        response = lote.enviar(request=None)
        self.assertEqual(response["retorno"], "error")
        self.assertIn("Ops", response["mensagem"])

    def test_enviar_erro_generico_com_request_chama_message_error(self):
        lote = self._build_lote()
        lote.quant_eventos = MagicMock(return_value=math.nan)

        with patch("apps.esocial.models.lote.messages.error") as error_mock:
            response = lote.enviar(request=SimpleNamespace())

        self.assertEqual(response["retorno"], "error")
        error_mock.assert_called_once()

    def test_enviar_retorna_erro_no_envio_quando_codigo_resposta_invalido(self):
        lote = self._build_lote()
        lote.quant_eventos = MagicMock(return_value=ESOCIAL_LOTE_MIN)
        lote._enviar = MagicMock(return_value=("<xml/>", "<batch/>"))

        response_dict = {
            "eSocial": {
                "retornoEnvioLoteEventos": {
                    "status": {"cdResposta": "500", "descResposta": "Falha"}
                }
            }
        }

        with patch("apps.esocial.models.lote.xmltodict.parse", return_value=response_dict):
            with patch("apps.esocial.models.lote.messages.error"):
                response = lote.enviar(request=SimpleNamespace())

        self.assertEqual(response["retorno"], "error")
        self.assertEqual(lote.status, STATUS_TRANSMISSOR_ERRO_ENVIO)
        lote.save.assert_called()

    def test_enviar_erro_no_envio_sem_request_cobre_branch_false(self):
        lote = self._build_lote()
        lote.quant_eventos = MagicMock(return_value=ESOCIAL_LOTE_MIN)
        lote._enviar = MagicMock(return_value=("<xml/>", "<batch/>"))

        response_dict = {
            "eSocial": {
                "retornoEnvioLoteEventos": {
                    "status": {"cdResposta": "500", "descResposta": "Falha"}
                }
            }
        }

        with patch("apps.esocial.models.lote.xmltodict.parse", return_value=response_dict):
            response = lote.enviar(request=None)

        self.assertEqual(response["retorno"], "error")

    def test_enviar_retorna_sucesso_e_atualiza_eventos(self):
        lote = self._build_lote()
        lote.quant_eventos = MagicMock(return_value=ESOCIAL_LOTE_MIN)
        lote._enviar = MagicMock(return_value=("<xml/>", "<batch/>"))

        response_dict = {
            "eSocial": {
                "retornoEnvioLoteEventos": {
                    "status": {"cdResposta": "201", "descResposta": "OK"},
                    "dadosRecepcaoLote": {
                        "dhRecepcao": "2024-01-01T00:00:00",
                        "versaoAplicativoRecepcao": "v1",
                        "protocoloEnvio": "PROTO",
                    },
                }
            }
        }

        with patch("apps.esocial.models.lote.xmltodict.parse", return_value=response_dict):
            with patch("apps.esocial.models.lote.messages.success"), \
                    patch.object(Lotes, "transmissor_esocial", new=MagicMock()) as rel_manager:
                response = lote.enviar(request=SimpleNamespace())

        self.assertEqual(response["retorno"], "success")
        self.assertEqual(lote.status, STATUS_TRANSMISSOR_ENVIADO)
        rel_manager.update.assert_called_once()

    def test_enviar_sucesso_sem_request_cobre_branch_false(self):
        lote = self._build_lote()
        lote.quant_eventos = MagicMock(return_value=ESOCIAL_LOTE_MIN)
        lote._enviar = MagicMock(return_value=("<xml/>", "<batch/>"))

        response_dict = {
            "eSocial": {
                "retornoEnvioLoteEventos": {
                    "status": {"cdResposta": "201", "descResposta": "OK"},
                    "dadosRecepcaoLote": {
                        "dhRecepcao": "2024-01-01T00:00:00",
                        "versaoAplicativoRecepcao": "v1",
                        "protocoloEnvio": "PROTO",
                    },
                }
            }
        }

        with patch("apps.esocial.models.lote.xmltodict.parse", return_value=response_dict):
            with patch.object(Lotes, "transmissor_esocial", new=MagicMock()) as rel_manager:
                response = lote.enviar(request=None)

        self.assertEqual(response["retorno"], "success")
        rel_manager.update.assert_called_once()

    def test__consultar_cria_ws_client_e_retorna_xml(self):
        lote = self._build_lote()

        fake_esocial = ModuleType("esocial")
        fake_xml = ModuleType("esocial.xml")
        fake_client = ModuleType("esocial.client")

        ws_client = MagicMock()
        ws_client.retrieve.return_value = "RETRIEVE_OBJ"
        fake_client.WSClient = MagicMock(return_value=ws_client)
        fake_xml.dump_tostring = MagicMock(return_value="RETRIEVE_XML")
        fake_esocial.xml = fake_xml
        fake_esocial.client = fake_client

        with patch.dict(
            sys.modules,
            {"esocial": fake_esocial, "esocial.xml": fake_xml, "esocial.client": fake_client},
        ):
            result = lote._consultar()

        self.assertEqual(result, "RETRIEVE_XML")
        ws_client.retrieve.assert_called_once_with(protocol_number=lote.protocolo)

    def test_consultar_retorna_erro_quando_nao_ha_protocolo(self):
        lote = self._build_lote()
        lote.protocolo = ""

        response = lote.consultar()
        self.assertEqual(response["retorno"], "error")
        self.assertIn("protocolo", response["mensagem"])

    def test_consultar_retorna_erro_quando_precondicoes_invalidas(self):
        lote = self._build_lote()
        lote.status = 999

        response = lote.consultar()
        self.assertEqual(response["retorno"], "error")
        self.assertIn("certificado", response["mensagem"])

    def test_consultar_retorna_none_quando_codigo_101(self):
        lote = self._build_lote()
        lote.status = STATUS_TRANSMISSOR_ENVIADO
        lote._consultar = MagicMock(return_value="<xml/>")

        response_dict = {
            "eSocial": {
                "retornoProcessamentoLoteEventos": {
                    "status": {"cdResposta": "101", "descResposta": "Aguardando"},
                    "dadosProcessamentoLote": {},
                }
            }
        }

        with patch("apps.esocial.models.lote.xmltodict.parse", return_value=response_dict):
            result = lote.consultar()

        self.assertIsNone(result)
        self.assertEqual(lote.status, STATUS_TRANSMISSOR_ENVIADO)

    def test_consultar_retorna_none_quando_codigo_de_erro(self):
        lote = self._build_lote()
        lote.status = STATUS_TRANSMISSOR_ENVIADO
        lote._consultar = MagicMock(return_value="<xml/>")

        response_dict = {
            "eSocial": {
                "retornoProcessamentoLoteEventos": {
                    "status": {"cdResposta": "500", "descResposta": "Erro"},
                    "dadosProcessamentoLote": {},
                }
            }
        }

        with patch("apps.esocial.models.lote.xmltodict.parse", return_value=response_dict):
            result = lote.consultar()

        self.assertIsNone(result)
        self.assertEqual(lote.status, STATUS_TRANSMISSOR_ERRO_CONSULTA)

    def test_consultar_processa_evento_dict_com_ocorrencias_dict(self):
        lote = self._build_lote()
        lote.status = STATUS_TRANSMISSOR_ENVIADO
        lote._consultar = MagicMock(return_value="<xml/>")

        code_processed = str(next(iter(CODIGOS_RESPOSTA_PROCESSADOS)))
        response_dict = {
            "eSocial": {
                "retornoProcessamentoLoteEventos": {
                    "status": {"cdResposta": "201", "descResposta": "OK"},
                    "dadosProcessamentoLote": {
                        "versaoAplicativoProcessamentoLote": "1.0",
                    },
                    "retornoEventos": {
                        "evento": {
                            "@Id": "ID-1",
                            "retornoEvento": {
                                "eSocial": {
                                    "retornoEvento": {
                                        "processamento": {
                                            "cdResposta": code_processed,
                                            "ocorrencias": {"ocorrencia": {"tipo": 1}},
                                        }
                                    }
                                }
                            },
                        }
                    },
                }
            }
        }

        evento = SimpleNamespace(status=None, save=MagicMock())

        with patch("apps.esocial.models.lote.xmltodict.parse", return_value=response_dict), \
                patch("apps.esocial.models.evento.Eventos.objects.get", return_value=evento):
            result = lote.consultar()

        self.assertEqual(result["retorno"], "success")
        self.assertEqual(evento.status, STATUS_EVENTO_PROCESSADO)
        evento.save.assert_called_once()

    def test_consultar_processa_eventos_lista_com_codigos_varios(self):
        lote = self._build_lote()
        lote.status = STATUS_TRANSMISSOR_ENVIADO
        lote._consultar = MagicMock(return_value="<xml/>")

        code_processed = str(next(iter(CODIGOS_RESPOSTA_PROCESSADOS)))
        response_dict = {
            "eSocial": {
                "retornoProcessamentoLoteEventos": {
                    "status": {"cdResposta": "201", "descResposta": "OK"},
                    "dadosProcessamentoLote": {},
                    "retornoEventos": {
                        "evento": [
                            {
                                "@Id": "ID-1",
                                "retornoEvento": {
                                    "eSocial": {
                                        "retornoEvento": {
                                            "processamento": {"cdResposta": code_processed}
                                        }
                                    }
                                },
                            },
                            {
                                "@Id": "ID-2",
                                "retornoEvento": {
                                    "eSocial": {
                                        "retornoEvento": {
                                            "processamento": {
                                                "cdResposta": CODIGO_AGUARDANDO_PROCESSAMENTO
                                            }
                                        }
                                    }
                                },
                            },
                            {
                                "@Id": "ID-3",
                                "retornoEvento": {
                                    "eSocial": {
                                        "retornoEvento": {"processamento": {"cdResposta": "500"}}
                                    }
                                },
                            },
                        ]
                    },
                }
            }
        }

        events = {
            "ID-1": SimpleNamespace(status=None, save=MagicMock()),
            "ID-2": SimpleNamespace(status=None, save=MagicMock(), identidade="ID-2"),
            "ID-3": SimpleNamespace(status=None, save=MagicMock()),
        }

        def get_evento(identidade):
            return events[identidade]

        with patch("apps.esocial.models.lote.xmltodict.parse", return_value=response_dict), \
                patch("apps.esocial.models.evento.Eventos.objects.get", side_effect=get_evento):
            result = lote.consultar()

        self.assertEqual(result["retorno"], "success")
        self.assertEqual(events["ID-1"].status, STATUS_EVENTO_PROCESSADO)
        self.assertIsNone(events["ID-2"].status)
        self.assertEqual(events["ID-3"].status, STATUS_EVENTO_ERRO)

    def test_consultar_sem_eventos_atualiza_relacao_transmissor_esocial(self):
        lote = self._build_lote()
        lote.status = STATUS_TRANSMISSOR_ENVIADO
        lote._consultar = MagicMock(return_value="<xml/>")

        response_dict = {
            "eSocial": {
                "retornoProcessamentoLoteEventos": {
                    "status": {"cdResposta": "201", "descResposta": "OK"},
                    "dadosProcessamentoLote": {},
                    "retornoEventos": {"evento": []},
                }
            }
        }

        with patch("apps.esocial.models.lote.xmltodict.parse", return_value=response_dict):
            with patch.object(Lotes, "transmissor_esocial", new=MagicMock()) as rel_manager:
                result = lote.consultar()

        self.assertEqual(result["retorno"], "success")
        rel_manager.update.assert_called_once()

    def test_str_retorna_id_e_nome_empresa(self):
        lote = self._build_lote()
        self.assertIn("10 - Empresa Teste", str(lote))
