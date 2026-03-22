from django.contrib import admin, messages

from apps.esocial.choices import STATUS_TRANSMISSOR_AGUARDANDO
from apps.esocial.models import Eventos, Lotes
from config.mixins import AuditoriaAdminEventos, AuditoriaAdminInline


class EventosInline(AuditoriaAdminInline):
    classes = ['collapse']
    model = Eventos
    fields = (
        'identidade',
        'versao',
        'evento',
        'operacao',
        'status',
    )

    def has_add_permission(
            self,
            request,
            obj=None):
        return False

    def has_change_permission(
            self,
            request,
            obj=None):
        return False


@admin.register(Lotes)
class LotesAdmin(AuditoriaAdminEventos):

    def autorizar_envio(
            modeladmin,
            request,
            queryset):
        for obj in queryset:
            obj.status = STATUS_TRANSMISSOR_AGUARDANDO
            obj.save()

    setattr(autorizar_envio, 'short_description', 'Autorizar envio de lote')

    def enviar_lote(
            modeladmin,
            request,
            queryset):
        for obj in queryset:
            retorno = obj.enviar()
            retorno['id'] = obj.id
            # self.stdout.write('\n%(id)s %(status)s: %(mensagem)s' % retorno)
            messages.add_message(
                request, messages.INFO, '%(id)s %(retorno)s: %(mensagem)s' % retorno)

    setattr(enviar_lote, 'short_description', 'Enviar lote')

    def consultar_lote(
            modeladmin,
            request,
            queryset):
        for obj in queryset:
            retorno = obj.consultar()
            retorno['id'] = obj.id
            messages.add_message(
                request, messages.INFO, '%(id)s %(retorno)s: %(mensagem)s' % retorno)

    setattr(consultar_lote, 'short_description', 'Consultar lote')

    actions = [
        autorizar_envio,
        enviar_lote,
        consultar_lote,
    ]
    inlines = (
        EventosInline,
    )
    search_fields = (
        'transmissor',
        'empregador_tpinsc',
        'empregador_nrinsc',
        'grupo',
        'status',
        'resposta_codigo',
        'resposta_descricao',
        'recepcao_data_hora',
        'recepcao_versao_aplicativo',
        'protocolo',
        'processamento_versao_aplicativo',
        'tempo_estimado_conclusao',
        'data_hora_envio',
        'data_hora_consulta',
    )

    list_filter = (
        'transmissor',
        'empregador_tpinsc',
        'empregador_nrinsc',
        'grupo',
        'status',)
    list_display = (
        'id',
        'transmissor',
        'empregador_tpinsc',
        'empregador_nrinsc',
        'grupo',
        'status',
        'resposta_codigo',
        'resposta_descricao',
        'recepcao_data_hora',
        'recepcao_versao_aplicativo',
        'protocolo',
        'data_hora_envio',
        'data_hora_consulta',
    )
    fieldsets = (
        (None, {
            'fields': (
                'transmissor',
                'grupo',
                'empregador_tpinsc',
                'empregador_nrinsc',
                'status',
                'resposta_codigo',
                'resposta_descricao',
                'data_hora_envio',
                'data_hora_consulta',
                'recepcao_data_hora',
                'recepcao_versao_aplicativo',
                'protocolo',
                'processamento_versao_aplicativo',
                'tempo_estimado_conclusao',
                'created_at',
                'created_by',
                'updated_at',
                'updated_by',
                'batch_xml',
                'response_send_xml',
                'response_retrieve_xml',
            ),
        }),
    )

    def has_add_permission(
            self,
            request,
            obj=None):
        return False

    def has_change_permission(
            self,
            request,
            obj=None):
        return False
