import json
from typing import Any, Dict

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from apps.esocial.models import Eventos


def set_nested_value(
        d,
        keys,
        value):
    """
    Insere um valor em um dicionário aninhado baseado em uma lista de chaves.
    """
    for key in keys[:-1]:
        if key not in d:
            d[key] = {}
        d = d[key]
    d[keys[-1]] = value


def transform_to_list(
        input_dict):
    """
    Transforma um dicionário no formato de índices (ex: '0', '1') em uma lista
    de dicionários, reorganizando os valores aninhados.
    """
    result = {}

    for key, value in input_dict.items():
        if isinstance(value, dict):
            # Verifica se todas as chaves do dicionário são numéricas
            if all(k.isdigit() for k in value.keys()):
                # Converte o dicionário em uma lista de dicionários
                result[key] = [
                    dict(value[idx].items())
                    for idx in sorted(value.keys(), key=int)
                ]
            else:
                # Continua o processamento recursivo caso seja outro dicionário
                result[key] = transform_to_list(value)
        else:
            result[key] = value

    return result


def parsing_post_to_json(
        form_data):
    json_data: Dict[str, Any] = {}
    for item in form_data:
        if '[' in item:
            keys = [key.replace("[", "").replace("]", "") for key in item.split("][")]
            set_nested_value(json_data, keys, form_data[item])
    transformed_data = transform_to_list(json_data)
    return transformed_data


@login_required
def parsing_post(
        request,
        pk):
    evento = get_object_or_404(Eventos, pk=pk)
    response = {}
    if request.method == 'POST':
        data = json.loads(request.body)
        response = parsing_post_to_json(data)
        evento.evento_json = json.dumps(response)
        evento.save()
    return HttpResponse(
        json.dumps(response), content_type='application/json')
