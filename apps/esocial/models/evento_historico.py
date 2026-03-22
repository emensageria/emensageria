from django.db import models

from apps.esocial.choices import CHOICES_INSCRICOESTIPOS, CHOICES_PROCEMI, CHOICES_TPAMB, \
    ESOCIAL_VERSAO_DEFAULT, \
    EVENTOS, \
    EVENTO_ORIGEM, EVENTO_ORIGEM_SISTEMA, EVENTO_STATUS, OPERACOES, \
    SIM_NAO, STATUS_EVENTO_CADASTRADO, VERSOES
from config.mixins import BaseModelEsocial


class EventosHistorico(BaseModelEsocial):
    cols = {
        'evento': 8,
        'evento_json': 12,
    }
    evt = models.ForeignKey(
        'Eventos',
        on_delete=models.SET_NULL,
        verbose_name='Evento',
        related_name='evento_esocial',
        blank=True, null=True, )
    identidade = models.CharField(
        'Identidade',
        max_length=36,
        blank=True, )
    versao = models.CharField(
        'Versão',
        choices=VERSOES,
        max_length=20,
        default=ESOCIAL_VERSAO_DEFAULT, )
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
        'Numero de inscrição',
        max_length=15, )
    tpamb = models.IntegerField(
        'Identificação do ambiente',
        choices=CHOICES_TPAMB, null=True, )
    procemi = models.IntegerField(
        'Processo de emissão do evento',
        choices=CHOICES_PROCEMI, null=True, default=1, )
    verproc = models.CharField(
        'Versão do processo', max_length=20, blank=True, )
    lote = models.ForeignKey(
        'Lotes',
        on_delete=models.SET_NULL,
        verbose_name='Transmissor',
        related_name='transmissor_esocial_historico',
        blank=True, null=True, )
    certificado = models.ForeignKey(
        'Certificados',
        on_delete=models.SET_NULL,
        verbose_name='Certificado',
        related_name='certificado_esocial_historico',
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

    def __str__(
            self):
        return self.identidade

    class Meta:
        verbose_name = 'Histórico do Evento'
        verbose_name_plural = 'Histórico dos Eventos'
        ordering = [
            '-id', ]
