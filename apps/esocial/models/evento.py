import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import esocial.utils
from django.conf import settings
from django.contrib import messages
from django.db import models
from django.forms import model_to_dict
from esocial.xml import load_fromstring, sign
from lxml import etree

from apps.esocial.choices import (
    CHOICES_INSCRICOESTIPOS, CHOICES_PROCEMI, CHOICES_TPAMB, EVENTOS,
    EVENTOS_GRUPOS_NAO_PERIODICOS,
    EVENTOS_GRUPOS_PERIODICOS, EVENTOS_GRUPOS_TABELAS, EVENTO_COD, EVENTO_ORIGEM, EVENTO_ORIGEM_API,
    EVENTO_ORIGEM_SISTEMA, EVENTO_STATUS, OPERACOES, SIM_NAO, STATUS_EVENTO_AGUARD_ENVIO,
    STATUS_EVENTO_CADASTRADO, STATUS_EVENTO_ERRO, STATUS_EVENTO_IMPORTADO,
    STATUS_TRANSMISSOR_AGUARDANDO, STATUS_TRANSMISSOR_CADASTRADO, VERSOES)
from config.functions import save_file
from config.mixins import BaseModelEsocial
from config.settings import BASE_DIR, VALIDAR_SCHEMA, VERSAO_LAYOUT_ESOCIAL

logger = logging.getLogger("django")


class Eventos(BaseModelEsocial):
    cols = {
        'versao': 2,
        'evento': 4,
        'operacao': 3,
        'identidade': 3,
        'evento_json': 12,
        'certificado': 4,
        'tpinsc': 4,
        'nrinsc': 8,
    }
    identidade = models.CharField(
        'Identidade',
        max_length=36,
        blank=True,
        null=True,
        unique=True)
    versao = models.CharField(
        'Versão',
        choices=VERSOES,
        max_length=20,
        default=VERSAO_LAYOUT_ESOCIAL, )
    evento = models.CharField(
        'Evento',
        choices=EVENTOS,
        max_length=20, )
    operacao = models.IntegerField(
        'Operações',
        choices=OPERACOES,
        blank=True, null=True, )
    status = models.IntegerField(
        'Status',
        choices=EVENTO_STATUS,
        blank=True,
        default=STATUS_EVENTO_CADASTRADO, )
    tpinsc = models.IntegerField(
        'Tipo de inscrição',
        choices=CHOICES_INSCRICOESTIPOS)
    nrinsc = models.CharField(
        'Número de inscrição',
        max_length=15,
        help_text="O CNPJ completo somente pode ser utilizado por órgãos públicos, "
                  "os demais empregadores deverão informar somente o CNPJ base"
                  " (8 primeiros dígitos do CNPJ)")
    tpamb = models.IntegerField(
        'Identificação do ambiente',
        choices=CHOICES_TPAMB, default=settings.ESOCIAL_TPAMB)
    procemi = models.IntegerField(
        'Processo de emissão do evento',
        choices=CHOICES_PROCEMI, default=settings.ESOCIAL_PROCEMI, )
    verproc = models.CharField(
        'Versão do processo',
        max_length=20, blank=True, default=settings.VERSAO_EMENSAGERIA, )
    certificado = models.ForeignKey(
        'Certificados',
        on_delete=models.PROTECT,
        verbose_name='Certificado',
        related_name='certificado_esocial',
        blank=True, null=True, )

    #####

    lote = models.ForeignKey(
        'Lotes',
        on_delete=models.PROTECT,
        verbose_name='Lote/Transmissor',
        related_name='transmissor_esocial',
        blank=True, null=True, )

    validacao_precedencia = models.IntegerField(
        'Validação de precedência',
        choices=SIM_NAO, blank=True, null=True, )

    validacoes = models.TextField(
        'Validações', blank=True, )

    arquivo = models.CharField(
        'Arquivo', max_length=200, blank=True, )

    retorno_envio_json = models.JSONField(
        'Retorno do envio', null=True, default=dict, blank=True)
    retorno_consulta_json = models.JSONField(
        'Retorno da consulta', null=True, default=dict, blank=True)
    retorno_envio_lote_json = models.JSONField(
        'Retorno do lote do envio', null=True, default=dict, blank=True)
    retorno_consulta_lote_json = models.JSONField(
        'Retorno do lote da consulta', null=True, default=dict, blank=True)
    evento_json = models.JSONField("JSON", null=True, default=dict, blank=True)
    evento_xml = models.TextField("XML", blank=True)
    ocorrencias_json = models.JSONField("Ocorrências", default=dict, null=True, blank=True)
    origem = models.IntegerField(
        'Origem do evento',
        choices=EVENTO_ORIGEM, default=EVENTO_ORIGEM_SISTEMA, )
    is_aberto = models.BooleanField(
        'Está aberto para edição', default=True, )

    def is_editable(
            self):
        file_path = Path(
            os.path.join(
                str(BASE_DIR),
                'apps',
                'esocial',
                'templates',
                self.versao,
                f'{self.evento}.html'))

        if file_path.is_file():
            return True
        return False

    def get_grupo_esocial(
            self):
        if self.evento in ['s1000', 's1005', 's1010', 's1020', 's1070']:
            return EVENTOS_GRUPOS_TABELAS
        elif self.evento in ['s1200', 's1202', 's1207', 's1210', 's1260', 's1270', 's1280', 's1298',
                             's1299']:
            return EVENTOS_GRUPOS_PERIODICOS
        else:
            return EVENTOS_GRUPOS_NAO_PERIODICOS

    def retorno_envio(
            self):
        return self.retorno_envio_json or {}

    def retorno_consulta(
            self):
        return self.retorno_consulta_json or {}

    def retorno_envio_lote(
            self):
        return self.retorno_envio_lote_json or {}

    def retorno_consulta_lote(
            self):
        return self.retorno_consulta_lote_json or {}

    def ocorrencias(
            self):
        return self.ocorrencias_json or {}

    def __str__(
            self):
        return self.identidade

    def replace_id(self, xml_str: str, new_id: str) -> str:
        """
        Substitui a primeira ocorrência de Id="ID..." no xml_str por Id="new_id".
        Se não encontrar nada, levanta ValueError.
        """
        # Captura:
        #  (Id=")    → prefixo até o início do valor
        #  ID[^"]*   → ID + tudo até a próxima aspa
        #  (")       → aspa de fechamento
        pattern = r'(Id=")ID[^"]*(")'
        replacement = rf'\1{new_id}\2'

        # faz somente uma substituição
        new_xml, _ = re.subn(pattern, replacement, xml_str, count=1)
        return new_xml

    def make_identidade(
            self,
            request=None):
        existe = True
        num = 0
        while existe:
            num += 1
            identidade_temp = 'ID{}{:0<14}{}{:0>5}'.format(
                self.tpinsc,
                self.nrinsc,
                self.created_at.strftime('%Y%m%d%H%M%S'),
                num)
            lista_eventos = Eventos.objects.exclude(id=self.id). \
                filter(identidade=identidade_temp).all()
            if not lista_eventos:
                self.identidade = identidade_temp
                if self.evento_xml:
                    self.evento_xml = self.replace_id(self.evento_xml, identidade_temp)
                self.save()
                existe = False
        return identidade_temp

    def xsd_file(
            self):
        return os.path.join(
            settings.BASE_DIR,
            'xsd',
            'esocial',
            self.versao,
            '{}.xsd'.format(EVENTO_COD[self.evento]['codigo']))

    def pdf_file(
            self):
        return os.path.join(
            settings.MEDIA_ROOT,
            'recibos', 'esocial', '{}.pdf'.format(self.identidade))

    def xml_file(
            self, timestamp=None):
        if timestamp:
            return os.path.join(
                settings.MEDIA_ROOT,
                'eventos', 'esocial', '{}_{}.xml'.format(self.identidade, timestamp))
        return os.path.join(
            settings.MEDIA_ROOT,
            'eventos', 'esocial', '{}.xml'.format(self.identidade))

    def _get_transmissor(
            self):
        from apps.esocial.models import Transmissor

        transmissores = Transmissor.objects.filter(nrinsc=self.nrinsc).all()
        if transmissores:
            return transmissores[0]
        return None

    def _get_lote_aguardando(
            self,
            transmissor):
        from apps.esocial.models import Lotes

        lotes = Lotes.objects.filter(
            empregador_tpinsc=transmissor.tpinsc,
            empregador_nrinsc=transmissor.nrinsc,
            grupo=self.get_grupo_esocial(),
            status=STATUS_TRANSMISSOR_AGUARDANDO,
        ).all()[:50]
        for lote in lotes:
            eventos = Eventos.objects.filter(lote=lote).all()
            if len(eventos) < settings.ESOCIAL_LOTE_MAX:
                return lote
        return None

    def _criar_lote(
            self,
            transmissor):
        from apps.esocial.models import Lotes

        lote = Lotes(
            transmissor=transmissor,
            empregador_tpinsc=transmissor.tpinsc,
            empregador_nrinsc=transmissor.nrinsc,
            grupo=self.get_grupo_esocial(),
            status=STATUS_TRANSMISSOR_CADASTRADO,
        )
        lote.save()
        return lote

    def _notify_transmissor_nao_encontrado(
            self,
            request):
        if request:
            messages.error(
                request,
                'Erro ao vincular evento. Não foi encontrado nenhum transmissor'
                ' com o número de inscrição: %s!' % self.nrinsc)

    def vincular_transmissor(
            self,
            request=None):
        if self.lote:
            return None

        transmissor = self._get_transmissor()
        if not transmissor:
            self._notify_transmissor_nao_encontrado(request)
            return None

        lote = self._get_lote_aguardando(transmissor) or self._criar_lote(transmissor)
        self.lote = lote
        self.save()
        return lote

    def enviar(
            self,
            request=None):
        from apps.esocial.models import Transmissor, Lotes
        tra = Transmissor.objects. \
            get(nrinsc=self.nrinsc)
        if self.lote and self.lote.transmissor == tra:
            return self.lote.enviar()
        tra_evt_data = {
            'transmissor': tra,
            'empregador_tpinsc': tra.tpinsc,
            'empregador_nrinsc': tra.nrinsc,
            'grupo': self.get_grupo_esocial(),
            'status': STATUS_TRANSMISSOR_CADASTRADO,
        }
        tra_evt = Lotes(**tra_evt_data)
        tra_evt.save()
        self.lote = tra_evt
        self.save()
        return tra_evt.enviar()

    def consultar(
            self,
            request=None):
        if self.lote:
            return self.lote.consultar()
        else:
            return {}

    def salvar_certificado_transmissor(self):
        if self.lote and self.lote.transmissor:
            self.certificado = self.lote.transmissor.certificado
            self.save()

    def _persistir_evento_xml(
            self,
            evento_xml,
            timestamp):
        self.evento_xml = evento_xml
        self.save()
        Eventos.objects.filter(id=self.id).update(evento_xml=evento_xml)
        save_file(self.xml_file(), evento_xml)
        save_file(self.xml_file(timestamp), evento_xml)

    def _xml_namespace(
            self,
            evento_codigo):
        return f"http://www.esocial.gov.br/schema/evt/{evento_codigo}/{self.versao}"

    def _find_event_element(
            self,
            xml_obj,
            evt_tag):
        elem = xml_obj.find(f'.//{evt_tag}')
        if elem is None:
            elem = xml_obj.find(f'.//{{*}}{evt_tag}')
        if elem is None:
            raise ValueError(f"Elemento <{evt_tag}> não encontrado no XML.")
        return elem

    @staticmethod
    def _flatten_duplicate_tags(
            et_module,
            xml_str):
        root = et_module.fromstring(xml_str)

        def remove_redundant_containers(elem):
            for child in elem:
                remove_redundant_containers(child)

            novos_filhos = []
            for child in elem:
                if len(child) > 0 and all(grandchild.tag == child.tag for grandchild in child):
                    novos_filhos.extend(child)
                else:
                    novos_filhos.append(child)
            elem[:] = novos_filhos

        remove_redundant_containers(root)
        return et_module.tostring(root, encoding='unicode')

    @staticmethod
    def _recursive_update_datefield(
            elem2):
        from dateutil import parser as dateutil_parser

        for elem in elem2:
            if elem.text and len(elem.text) == 10 and len(elem.text.split('/')) == 3:
                data = dateutil_parser.parse(elem.text, dayfirst=True)
                elem.text = data.strftime('%Y-%m-%d')
            else:
                Eventos._recursive_update_datefield(elem)

    @staticmethod
    def _recursive_remove_empty(
            elem2):
        for elem in tuple(elem2):
            if len(elem) == 0 and (elem.text is None or not elem.text.strip()):
                elem2.remove(elem)
            else:
                Eventos._recursive_remove_empty(elem)

    @staticmethod
    def _has_empty_tags(
            xml_obj):
        for elem in xml_obj.iter():
            if len(elem) == 0 and (elem.text is None or not elem.text.strip()):
                return True
        return False

    def _cleanup_xml_object(
            self,
            xml_obj):
        while self._has_empty_tags(xml_obj):
            for elem in tuple(xml_obj):
                self._recursive_update_datefield(elem)
                self._recursive_remove_empty(elem)

    def _ensure_imported_xml_ready(
            self,
            et_module,
            xml_str,
            evento_codigo):
        xml_changed = False
        if '<eSocial' not in xml_str:
            logger.info(f"Incluindo a tag eSocial no evento {self.id}.")
            xml_str = '<eSocial>' + xml_str + '</eSocial>'
            xml_changed = True

        xml_obj = et_module.fromstring(xml_str)
        if 'www.esocial.gov.br/schema/evt' not in xml_str:
            logger.info(f"Incluindo o name space xmlns no evento {self.id}.")
            et_module.register_namespace("", self._xml_namespace(evento_codigo))
            xml_obj.set('xmlns', self._xml_namespace(evento_codigo))
            xml_changed = True

        if 'Id="ID' not in xml_str:
            logger.info(f"Incluindo o ID no evento {self.id}.")
            if not self.identidade:
                self.make_identidade()
            evt_tag = EVENTO_COD[self.evento]['codigo']
            self._find_event_element(xml_obj, evt_tag).set('Id', self.identidade)
            xml_changed = True

        if xml_changed:
            xml_str = et_module.tostring(xml_obj, encoding='utf-8').decode('utf-8')
        return xml_str

    def _create_xml_from_imported_xml(
            self,
            et_module,
            timestamp,
            evento_codigo,
            request):
        logger.info("XML criado a partir do campo evento_xml")
        xml_str = self._ensure_imported_xml_ready(
            et_module,
            self.evento_xml,
            evento_codigo,
        )
        self._persistir_evento_xml(xml_str, timestamp)
        if 'Signature' not in self.evento_xml:
            logger.info(f"Assinando o evento {self.id}.")
            self.assinar(request)

    def _create_xml_from_json(
            self,
            et_module,
            dicttoxml,
            timestamp,
            evento_codigo,
            request):
        logger.info("XML criado a partir do campo evento_json")
        xml = dicttoxml.dicttoxml(
            self.evento_json,
            attr_type=False,
            custom_root='eSocial',
            item_func=lambda x: x).decode()
        xml = self._flatten_duplicate_tags(et_module, xml)

        et_module.register_namespace("", self._xml_namespace(evento_codigo))
        xml_obj = et_module.fromstring(xml)
        xml_obj.set('xmlns', self._xml_namespace(evento_codigo))
        self._cleanup_xml_object(xml_obj)
        if self.identidade:
            xml_obj.find(
                EVENTO_COD[self.evento]['codigo']
            ).set('Id', self.identidade)  # type: ignore

        evento_xml = et_module.tostring(xml_obj).decode('utf-8')
        self._persistir_evento_xml(evento_xml, timestamp)
        self.assinar(request)

    def _pode_criar_xml_importado(
            self):
        return (
            self.evento_xml and
            self.origem == EVENTO_ORIGEM_API and
            self.status == STATUS_EVENTO_IMPORTADO
        )

    def _pode_criar_xml_de_json(
            self):
        importado_da_api = (
            not self.evento_xml and
            self.evento_json and
            self.origem == EVENTO_ORIGEM_API and
            self.status == STATUS_EVENTO_IMPORTADO
        )
        return importado_da_api or (
            self.status == STATUS_EVENTO_CADASTRADO and
            self.is_editable()
        )

    def assinar(
            self,
            request=None):
        logger.info(f"Assinando o evento {self.id}.")
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

        if not self.lote:
            self.vincular_transmissor()
        if self.lote and not self.certificado:
            self.salvar_certificado_transmissor()
        if self.lote and self.certificado:
            cert_data = esocial.utils.pkcs12_data(
                self.certificado.certificado.file.name,
                self.certificado.get_senha())
            evt = load_fromstring(self.evento_xml)
            evt_signed = sign(evt, cert_data)
            evt_signed_ = etree.tostring(evt_signed).decode("utf-8")
            self.evento_xml = evt_signed_
            self.save()
            save_file(self.xml_file(), evt_signed_)
            save_file(self.xml_file(timestamp), evt_signed_)
        else:
            if request:
                messages.error(
                    request,
                    'Erro ao vincular evento. Não foi encontrado nenhum'
                    ' transmissor com o número de inscrição: %s!' % self.nrinsc)

    def create_xml(
            self,
            request=None):
        import xml.etree.ElementTree as ET
        import dicttoxml
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        evento_codigo = EVENTO_COD[self.evento]['codigo']
        if self._pode_criar_xml_importado():
            self._create_xml_from_imported_xml(ET, timestamp, evento_codigo, request)
        elif self._pode_criar_xml_de_json():
            self._create_xml_from_json(ET, dicttoxml, timestamp, evento_codigo, request)

    def _set_validation_state(
            self,
            ocorrencias,
            status,
            lote):
        self.ocorrencias_json = ocorrencias
        self.is_aberto = False
        self.status = status
        self.lote = lote
        self.save()

    @staticmethod
    def _notify_validation_result(
            request,
            level,
            message):
        if request:
            getattr(messages, level)(request, message)

    @staticmethod
    def _build_validation_errors(
            errors):
        return [
            {
                'tipo': '1',
                'codigo': '-',
                'descricao': error.reason,
                'localizacao': error.path,
            }
            for error in errors
        ]

    def validar(
            self,
            request=None):
        from config.functions import validar_schema

        self.create_xml()
        if not VALIDAR_SCHEMA:
            self._set_validation_state(None, STATUS_EVENTO_AGUARD_ENVIO, self.lote)
            self._notify_validation_result(request, 'success', 'Evento criado sem validação!')
            return

        errors = validar_schema(self.xsd_file(), self.xml_file())
        if errors:
            self._set_validation_state(
                self._build_validation_errors(errors),
                STATUS_EVENTO_ERRO,
                None,
            )
            self._notify_validation_result(request, 'error', 'Erro na validação do evento!')
            return

        self._set_validation_state(None, STATUS_EVENTO_AGUARD_ENVIO, self.lote)
        self._notify_validation_result(request, 'success', 'Evento validado com sucesso!')

    def duplicar_evento(
            self,
            request=None):
        ev_new = self
        ev_new.status = STATUS_EVENTO_CADASTRADO
        ev_new.identidade = STATUS_EVENTO_CADASTRADO
        ev_new.lote = None
        ev_new.created_at = datetime.now()
        ev_new.updated_at = None
        ev_new.created_by = None
        ev_new.updated_by = None
        ev_new.id = None
        ev_new.save()
        return ev_new

    def abrir_evento_para_edicao_lista(
            self):
        return [
            STATUS_EVENTO_IMPORTADO,
            STATUS_EVENTO_CADASTRADO,
            STATUS_EVENTO_ERRO,
            STATUS_EVENTO_AGUARD_ENVIO,
            STATUS_EVENTO_ERRO
        ]

    def abrir_evento_para_edicao(
            self,
            request=None):
        status_list = self.abrir_evento_para_edicao_lista()
        if self.status in status_list:
            if self.status == STATUS_EVENTO_AGUARD_ENVIO or self.status == STATUS_EVENTO_IMPORTADO:
                self.status = STATUS_EVENTO_CADASTRADO
            self.is_aberto = True
            self.lote = None
            self.save()
            if request:
                messages.success(request, "Evento aberto para edição!")
        else:
            if request:
                messages.error(
                    request, '''
                    Não foi possível abrir o evento para edição! Somente é possível
                    abrir eventos com os seguintes status: "Cadastrado", "Importado", "Validado",
                    "Duplicado", "Erro na validação", "XML Assinado" ou "XML Gerado"
                    ou com o status "Enviado com sucesso" e os seguintes
                    códigos de resposta do servidor:
                    "401 - Lote Incorreto - Erro preenchimento" ou
                    "402 - Lote Incorreto - schema Inválido"!''')

    def save(
            self,
            force_insert=False,
            force_update=False,
            using=None,
            update_fields=None):
        super(Eventos, self).save(
            force_insert=False,
            force_update=False,
            using=None,
            update_fields=None)
        from apps.esocial.models import EventosHistorico
        if not self.identidade:
            self.make_identidade()
        evento = Eventos.objects.get(id=self.id)
        data_dict: Dict[str, Any] = model_to_dict(evento)
        data_dict['evt_id'] = self.pk or None
        data_dict['created_by_id'] = data_dict.pop('created_by', None)
        data_dict['certificado_id'] = data_dict.pop('certificado', None)
        data_dict['lote_id'] = data_dict.pop('lote', None)
        data_dict.pop('id', None)
        EventosHistorico(**data_dict).save()

    class Meta:
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'
        ordering = [
            '-id', ]
