import re

import xmltodict
from rest_framework.serializers import (CharField, JSONField, ModelSerializer, ValidationError)

from apps.esocial.choices import EVENTO_ORIGEM_API, STATUS_EVENTO_IMPORTADO, VERSIONS_CODE
from apps.esocial.models import (Transmissor, Lotes)
from apps.esocial.models.evento import Eventos


def remove_ns_prefixes(
        dictionary):
    """Remove namespaces from keys in a nested dictionary."""
    if isinstance(dictionary, dict):
        new_dict = {}
        for key, value in dictionary.items():
            # Remove prefix like ns0: or ns1:
            new_key = re.sub(r'ns\d+:', '', key)
            new_dict[new_key] = remove_ns_prefixes(value)
        return new_dict
    elif isinstance(dictionary, list):
        return [remove_ns_prefixes(item) for item in dictionary]
    return dictionary


class TransmissorSerializer(ModelSerializer):
    class Meta:
        model = Transmissor
        fields = '__all__'
        read_only_fields = ('created_by', 'updated_by', 'created_at', 'updated_at',)


class LotesSerializer(ModelSerializer):
    class Meta:
        model = Lotes
        fields = '__all__'


class EventosSerializer(ModelSerializer):
    retorno_envio = JSONField(read_only=True)
    retorno_consulta = JSONField(read_only=True)
    retorno_envio_lote = JSONField(read_only=True)
    retorno_consulta_lote = JSONField(read_only=True)
    ocorrencias = JSONField(read_only=True)
    status_txt = CharField(source='get_status_display', read_only=True)
    tpinsc_txt = CharField(source='get_tpinsc_display', read_only=True)
    tpamb_txt = CharField(source='get_tpamb_display', read_only=True)
    procemi_txt = CharField(source='get_procemi_display', read_only=True)
    origem_txt = CharField(source='get_origem_display', read_only=True)
    transmissor = LotesSerializer(
        source='lote', many=False, read_only=True)

    def create(
            self,
            validated_data):
        from config.settings import ESOCIAL_TPAMB
        validated_data['origem'] = EVENTO_ORIGEM_API
        validated_data['is_aberto'] = False
        validated_data['status'] = STATUS_EVENTO_IMPORTADO
        validated_data['tpamb'] = ESOCIAL_TPAMB
        if validated_data.get('evento_xml') and not validated_data['evento_json']:
            parsed_xml = xmltodict.parse(validated_data['evento_xml'])
            cleaned_dict = remove_ns_prefixes(parsed_xml)
            validated_data['evento_json'] = cleaned_dict.get(
                'eSocial') if cleaned_dict.get('eSocial') else cleaned_dict
        instance = super().create(validated_data)
        instance.create_xml()
        return instance

    def update(
            self,
            instance,
            validated_data):
        from config.settings import ESOCIAL_TPAMB
        validated_data['origem'] = EVENTO_ORIGEM_API
        validated_data['is_aberto'] = False
        validated_data['status'] = STATUS_EVENTO_IMPORTADO
        validated_data['ocorrencias_json'] = None
        validated_data['tpamb'] = ESOCIAL_TPAMB
        validated_data['retorno_envio_json'] = {}
        validated_data['retorno_consulta_json'] = {}
        if validated_data.get('evento_xml') and not validated_data['evento_json']:
            parsed_xml = xmltodict.parse(validated_data['evento_xml'])
            cleaned_dict = remove_ns_prefixes(parsed_xml)
            validated_data['evento_json'] = cleaned_dict.get(
                'eSocial') if cleaned_dict.get('eSocial') else cleaned_dict
        instance = super().update(instance, validated_data)
        instance.create_xml()
        return instance

    def validate(
            self,
            data):
        versao = data.get("versao")
        evento = data.get("evento")
        if evento not in VERSIONS_CODE[versao]:
            raise ValidationError(
                "Este evento nao é válido para esta versão do eSocial.")
        return data

    class Meta:
        model = Eventos
        fields = '__all__'
        read_only_fields = (
            'tpamb',
            'procemi',
            'status',
            'lote',
            'validacao_precedencia',
            'validacoes',
            'arquivo',
            'is_aberto',
            'origem',
            'retorno_envio',
            'retorno_envio_json',
            'retorno_envio_lote_json',
            'retorno_consulta',
            'retorno_consulta_json',
            'retorno_consulta_lote_json',
            'ocorrencias',
            'ocorrencias_json',
            'created_by',
        )
