import json
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List

import xmltodict
from django.conf import settings
from django.contrib import messages
from django.db import models

from apps.esocial.choices import CODIGOS_RESPOSTA_PROCESSADOS, \
    CODIGO_AGUARDANDO_PROCESSAMENTO, EVENTOS_GRUPOS, STATUS_EVENTO_AGUARD_ENVIO, \
    STATUS_EVENTO_ENVIADO, STATUS_EVENTO_ERRO, STATUS_EVENTO_PROCESSADO, \
    STATUS_TRANSMISSOR_CADASTRADO, \
    STATUS_TRANSMISSOR_CONSULTADO, STATUS_TRANSMISSOR_ENVIADO, \
    STATUS_TRANSMISSOR_ERRO_CONSULTA, STATUS_TRANSMISSOR_ERRO_ENVIO, \
    TIPO_INSCRICAO, \
    TRANSMISSOR_STATUS
from config.functions import create_dir, read_file
from config.mixins import BaseModelEsocial, BaseModelSerializer
from config.settings import ESOCIAL_LOTE_MAX, ESOCIAL_LOTE_MIN, ESOCIAL_TARGET, FILES_PATH

logger = logging.getLogger('django')


class Lotes(BaseModelEsocial):
    cols = {
        'transmissor': 8,
        'arquivo_header': 12,
        'arquivo_request': 12,
        'arquivo_response': 12,
        'retorno_envio_json': 12,
        'retorno_consulta_json': 12,
        'ocorrencias_json': 12,
        'created_at': 3,
        'created_by': 3,
        'updated_at': 3,
        'updated_by': 3,
        'batch_xml': 12,
        'response_send_xml': 12,
        'response_retrieve_xml': 12,
    }
    transmissor = models.ForeignKey(
        'Transmissor',
        on_delete=models.PROTECT,
        verbose_name='Transmissor',
        related_name='%(class)s_transmissor',
        blank=True, )  # Verificar se era bom tornar obrigatório
    empregador_tpinsc = models.IntegerField(
        'Tipo de inscrição do empregador', choices=TIPO_INSCRICAO, )
    empregador_nrinsc = models.CharField('Número de inscrição do empregador', max_length=15, )
    grupo = models.IntegerField('Grupo', choices=EVENTOS_GRUPOS, )
    status = models.IntegerField(
        'Status',
        choices=TRANSMISSOR_STATUS, blank=True, default=0, )
    resposta_codigo = models.CharField(
        'Código da Resposta', max_length=10, blank=True, )
    resposta_descricao = models.TextField('Descrição da resposta', blank=True, )
    data_hora_envio = models.DateTimeField('Data/Hora do envio', blank=True, null=True, )
    data_hora_consulta = models.DateTimeField('Data/Hora da consulta', blank=True, null=True, )
    recepcao_data_hora = models.DateTimeField('Data/Hora da recepção', blank=True, null=True, )
    recepcao_versao_aplicativo = models.CharField(
        'Versão do aplicativo de recepção',
        max_length=50, blank=True, )
    protocolo = models.CharField('Protocolo', max_length=50, blank=True, )
    processamento_versao_aplicativo = models.CharField(
        'Versão do aplicativo de processamento', max_length=50, blank=True, )
    tempo_estimado_conclusao = models.IntegerField(
        'Tempo estimado de conclusão', blank=True, null=True, )
    arquivo_header = models.CharField(
        'Arquivo header', max_length=200, blank=True, )
    arquivo_request = models.CharField(
        'Arquivo request', max_length=200, blank=True, )
    arquivo_response = models.CharField(
        'Arquivo response', max_length=200, blank=True, )
    retorno_envio_json = models.JSONField(
        "Retorno do envio", blank=True, null=True)
    retorno_consulta_json = models.JSONField(
        "Retorno da consulta", blank=True, null=True)
    ocorrencias_json = models.JSONField(
        "Ocorrências", blank=True, null=True)
    batch_xml = models.TextField(
        "Lote (XML)", blank=True)
    response_send_xml = models.TextField(
        "Retorno do envio (XML)", blank=True)
    response_retrieve_xml = models.TextField(
        "Retorno da consulta (XML)", blank=True)

    def save(
            self,
            force_insert=False,
            force_update=False,
            using=None,
            update_fields=None):
        self.empregador_nrinsc = re.sub(r'\D', '', self.empregador_nrinsc)
        super(Lotes, self).save(
            force_insert=False,
            force_update=False,
            using=None,
            update_fields=None)

    def quant_eventos(
            self):
        from apps.esocial.models.evento import Eventos
        return Eventos.objects.filter(
            lote_id=self.id,
            status=STATUS_EVENTO_AGUARD_ENVIO).count()

    def eventos(
            self):
        from apps.esocial.models.evento import Eventos
        evts_txt = ''
        evts = Eventos.objects.filter(
            lote=self.id,
            status=STATUS_EVENTO_AGUARD_ENVIO).all()
        for evt in evts:
            evts_txt += '<evento Id="{}">{}</evento>'.format(
                evt.identidade,
                read_file(evt.xml_file()))
        return evts_txt

    def get_eventos(
            self):
        from apps.esocial.models.evento import Eventos
        evts = Eventos.objects.filter(
            lote=self.id,
            status=STATUS_EVENTO_AGUARD_ENVIO).all()
        return evts

    def get_request(
            self,
            service,
            date_now):
        filename = os.path.join(
            settings.BASE_DIR,
            FILES_PATH, 'comunicacao',
            service, 'request',
            '{}_{}.xml'.format(
                self.id, datetime.now().strftime('%Y%m%d%H%M%S')))
        create_dir(filename)
        return filename

    def get_response(
            self,
            service,
            date_now):
        filename = os.path.join(
            settings.BASE_DIR,
            FILES_PATH, 'comunicacao',
            service, 'response',
            '{}_{}.xml'.format(
                self.id, datetime.now().strftime('%Y%m%d%H%M%S')))
        create_dir(filename)
        return filename

    def _enviar(self):
        import esocial.xml
        import esocial.client
        ide_empregador = {
            'tpInsc': self.empregador_tpinsc,
            'nrInsc': self.empregador_nrinsc,
        }

        ide_transmissor = {
            'tpInsc': self.transmissor.transmissor_tpinsc,
            'nrInsc': self.transmissor.transmissor_nrinsc,
        }

        esocial_ws = esocial.client.WSClient(
            pfx_file=self.transmissor.certificado.cert_host(),
            pfx_passw=self.transmissor.certificado.get_senha(),
            employer_id=ide_empregador,
            sender_id=ide_transmissor,
            target=ESOCIAL_TARGET,
        )
        eventos = self.get_eventos()
        for evento in eventos:
            evento1_grupo1 = esocial.xml.load_fromstring(evento.evento_xml)
            # Adicionando eventos ao lote. O evento já vai ser assinado usando o certificado
            # fornecido e validado contra o XSD do evento
            # Se gen_event_id == True, o Id do evento é gerado pela lib (default = False)
            esocial_ws.add_event(evento1_grupo1)

        result, batch_xml = esocial_ws.send(group_id=self.grupo)
        result_str = esocial.xml.dump_tostring(result, xml_declaration=False, pretty_print=True)
        batch_xml_str = esocial.xml.dump_tostring(
            batch_xml, xml_declaration=False, pretty_print=True)
        return result_str, batch_xml_str

    @staticmethod
    def _build_envio_message(
            codigo,
            descricao):
        return '{} {}'.format(codigo, descricao)

    @staticmethod
    def _notify_request(
            request,
            level,
            message):
        if request:
            getattr(messages, level)(request, message)

    def _envio_invalido(
            self,
            quant_eventos):
        return not (
            self.transmissor.certificado and
            quant_eventos and
            self.status == STATUS_TRANSMISSOR_CADASTRADO
        )

    def _build_envio_error(
            self,
            message,
            request=None):
        self._notify_request(request, 'error', message)
        return {
            'retorno': 'error',
            'mensagem': message,
        }

    def _parse_envio_response(
            self,
            result):
        response_dict: Dict[str, Any] = xmltodict.parse(result)
        response_dict = response_dict["eSocial"]["retornoEnvioLoteEventos"]
        dados_recepcao = response_dict.get("dadosRecepcaoLote") or {}
        return {
            'response_dict': response_dict,
            'ocorrencias_dict': response_dict.get("status", {}).get("ocorrencias") or {},
            'resposta_codigo': response_dict.get("status", {}).get("cdResposta"),
            'resposta_descricao': response_dict.get("status", {}).get("descResposta"),
            'recepcao_data_hora': dados_recepcao.get("dhRecepcao"),
            'recepcao_versao_aplicativo': dados_recepcao.get("versaoAplicativoRecepcao"),
            'protocolo': dados_recepcao.get("protocoloEnvio"),
        }

    def _persist_envio(
            self,
            parsed_response,
            batch_xml,
            result,
            service,
            date_now):
        self.retorno_envio_json = parsed_response['response_dict']
        self.resposta_codigo = parsed_response['resposta_codigo']
        self.resposta_descricao = parsed_response['resposta_descricao']
        self.ocorrencias_json = parsed_response['ocorrencias_dict']
        self.data_hora_envio = datetime.now()
        self.recepcao_data_hora = parsed_response['recepcao_data_hora']
        self.recepcao_versao_aplicativo = parsed_response['recepcao_versao_aplicativo']
        self.protocolo = parsed_response['protocolo']
        self.arquivo_request = self.get_request(service, date_now)
        self.arquivo_response = self.get_response(service, date_now)
        self.batch_xml = batch_xml
        self.response_send_xml = result

    def _build_envio_response(
            self,
            retorno,
            response_dict,
            ocorrencias_lista,
            mensagem):
        return {
            'retorno': retorno,
            'retorno_envio': response_dict,
            'ocorrencias': ocorrencias_lista,
            'mensagem': mensagem,
        }

    def _processar_envio(
            self,
            service,
            request,
            date_now):
        result, batch_xml = self._enviar()
        parsed_response = self._parse_envio_response(result)
        self._persist_envio(parsed_response, batch_xml, result, service, date_now)
        ocorrencias_lista: List[Dict] = []
        mensagem = self._build_envio_message(
            parsed_response['resposta_codigo'],
            parsed_response['resposta_descricao'],
        )
        status = parsed_response['response_dict']["status"]["cdResposta"]
        if status not in ('101', '201', '202', '203'):
            self.status = STATUS_TRANSMISSOR_ERRO_ENVIO
            self.save()
            self._notify_request(request, 'error', mensagem)
            return self._build_envio_response(
                'error',
                parsed_response['response_dict'],
                ocorrencias_lista,
                mensagem,
            )

        self.status = STATUS_TRANSMISSOR_ENVIADO
        self.save()
        self.transmissor_esocial.update(
            retorno_envio_json=parsed_response['response_dict'],
            retorno_consulta_json={},
            retorno_envio_lote_json=parsed_response['response_dict'],
            retorno_consulta_lote_json={},
            status=STATUS_EVENTO_ENVIADO)
        self._notify_request(request, 'success', mensagem)
        return self._build_envio_response(
            'success',
            parsed_response['response_dict'],
            ocorrencias_lista,
            mensagem,
        )

    def enviar(
            self,
            service='WsEnviarLoteEventos',
            request=None):
        date_now = datetime.now().strftime('%Y%m%d%H%M%S')
        quant_eventos = self.quant_eventos()
        if self._envio_invalido(quant_eventos):
            return self._build_envio_error(
                '''O certificado não está configurado ou não
                                possuem eventos validados para envio neste lote!''',
                request,
            )
        if ESOCIAL_LOTE_MIN <= quant_eventos <= ESOCIAL_LOTE_MAX:
            return self._processar_envio(service, request, date_now)
        if quant_eventos < ESOCIAL_LOTE_MIN:
            return self._build_envio_error(
                'Lote com quantidade inferior a mínima permitida!',
                request,
            )
        if quant_eventos > ESOCIAL_LOTE_MAX:
            return self._build_envio_error(
                'Lote com quantidade de eventos superior a máxima permitida!',
                request,
            )
        return self._build_envio_error(
            'Ops! Algo aconteceu!',
            request,
        )

    def _consultar(self):
        import esocial.xml
        import esocial.client
        ide_empregador = {
            'tpInsc': self.empregador_tpinsc,
            'nrInsc': self.empregador_nrinsc,
        }

        ide_transmissor = {
            'tpInsc': self.transmissor.transmissor_tpinsc,
            'nrInsc': self.transmissor.transmissor_nrinsc,
        }

        esocial_ws = esocial.client.WSClient(
            pfx_file=self.transmissor.certificado.cert_host(),
            pfx_passw=self.transmissor.certificado.get_senha(),
            employer_id=ide_empregador,
            sender_id=ide_transmissor,
            target=ESOCIAL_TARGET,
        )
        result = esocial_ws.retrieve(protocol_number=self.protocolo)
        result_str = esocial.xml.dump_tostring(result, xml_declaration=False, pretty_print=True)
        return result_str

    def _consulta_disponivel(
            self):
        return (
            self.transmissor.certificado and
            self.protocolo and
            self.status in [
                STATUS_TRANSMISSOR_ENVIADO,
                STATUS_TRANSMISSOR_ERRO_CONSULTA,
                STATUS_TRANSMISSOR_CONSULTADO,
            ]
        )

    def _persist_consulta(
            self,
            response_dict,
            result,
            service,
            date_now):
        response_json = json.dumps(response_dict)
        self.retorno_consulta_json = response_json
        self.data_hora_consulta = datetime.now()
        self.resposta_codigo = response_dict.get('status', {}).get('cdResposta')
        self.resposta_descricao = response_dict.get('status', {}).get('descResposta')
        self.processamento_versao_aplicativo = response_dict.get(
            'dadosProcessamentoLote', {}).get('versaoAplicativoProcessamentoLote')
        self.arquivo_response = self.get_response(service, date_now)
        self.response_retrieve_xml = result

    def _consulta_aguardando_processamento(
            self):
        logger.info(f"Código 101: Lote {self.id} aguardando processamento")
        self.status = STATUS_TRANSMISSOR_ENVIADO
        self.save()
        return None

    def _consulta_com_erro(self):
        self.status = STATUS_TRANSMISSOR_ERRO_CONSULTA
        self.save()
        return None

    def _normalizar_eventos_retorno(
            self,
            response_dict):
        eventos = response_dict.get('retornoEventos', {}).get('evento', [])
        if type(eventos) is dict:
            return [eventos]
        return eventos

    def _atualizar_evento_consultado(
            self,
            evento,
            identidade,
            retorno_consulta_dict):
        ocorrencias = retorno_consulta_dict.get(
            'processamento', {}).get('ocorrencias', {}).get('ocorrencia', [])
        if type(ocorrencias) is dict:
            ocorrencias = [ocorrencias]

        evento.retorno_consulta_json = retorno_consulta_dict
        evento.retorno_consulta_lote_json = {}
        evento.ocorrencias_json = ocorrencias
        codigo_retorno = retorno_consulta_dict.get('processamento', {}).get('cdResposta')
        if codigo_retorno in CODIGOS_RESPOSTA_PROCESSADOS:
            evento.status = STATUS_EVENTO_PROCESSADO
        elif codigo_retorno == CODIGO_AGUARDANDO_PROCESSAMENTO:
            logger.info(
                f"Evento aguardando processamento {evento.identidade}, {codigo_retorno}")
        else:
            evento.status = STATUS_EVENTO_ERRO
        evento.save()
        return {
            'identidade': identidade,
            'ocorrencias': ocorrencias,
        }

    def consultar(
            self,
            service='WsConsultarLoteEventos',
            request=None):
        from apps.esocial.models.evento import Eventos

        date_now = datetime.now().strftime('%Y%m%d%H%M%S')
        if not self.protocolo:
            return {
                'retorno': 'error',
                'mensagem': 'O transmissor ainda não possui um número de protocolo!'
            }
        if not self._consulta_disponivel():
            return {
                'retorno': 'error',
                'mensagem': 'O certificado não está configurado ou não possuem eventos'
                            'validados para envio neste lote!'
            }

        result = self._consultar()
        response_dict = xmltodict.parse(result)
        response_dict = response_dict['eSocial']['retornoProcessamentoLoteEventos']
        self._persist_consulta(response_dict, result, service, date_now)

        if self.resposta_codigo == '101':
            return self._consulta_aguardando_processamento()
        if self.resposta_codigo not in ['101', "201", "202", "203"]:
            return self._consulta_com_erro()

        self.status = STATUS_TRANSMISSOR_CONSULTADO
        self.save()
        ocorrencias_lista = []
        eventos = self._normalizar_eventos_retorno(response_dict)
        for evt in eventos:
            identidade = evt["@Id"]
            retorno_consulta_dict = evt["retornoEvento"]["eSocial"]["retornoEvento"]
            evento = Eventos.objects.get(identidade=identidade)
            ocorrencias_lista.append(
                self._atualizar_evento_consultado(evento, identidade, retorno_consulta_dict))

        if not eventos:
            # Neste caso não houve nenhuma ocorrencia o evento foi
            # transmitido corretamente
            self.transmissor_esocial.update(
                retorno_consulta_json={},
                retorno_consulta_lote_json=response_dict
            )

        return {
            'retorno': 'success',
            'retorno_consulta': response_dict,
            'ocorrencias': ocorrencias_lista,
            'mensagem': 'Lote consultado com sucesso!'
        }

    def __str__(
            self):
        return '{} - {}'.format(
            self.id,
            self.transmissor.nome_empresa, )

    class Meta:
        verbose_name = 'Lote'
        verbose_name_plural = 'Lotes'
        ordering = [
            '-id', ]


class LotesSerializer(BaseModelSerializer):
    class Meta:
        model = Lotes
