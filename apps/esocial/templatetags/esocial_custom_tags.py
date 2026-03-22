import json
import locale
import logging
import os
import re
from pathlib import Path

from django import template
from django.core.validators import EMPTY_VALUES

from config.settings import BASE_DIR

# Configura o logger
logger = logging.getLogger(__name__)

try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except Exception as e:
    logger.error("Erro ao definir locale 'pt_BR.UTF-8', tentando 'pt_BR.utf8': %s", e)
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR.utf8')
    except Exception as e:
        logger.critical("Falha ao definir locale 'pt_BR.utf8': %s", e)

register = template.Library()


def _build_ocorrencia_item(ocorrencia):
    return {
        'tipo': ocorrencia.get('tipo'),
        'codigo': ocorrencia.get('codigo'),
        'descricao': ocorrencia.get('descricao'),
        'localizacao': ocorrencia.get('localizacao'),
    }


def _normalize_ocorrencias(obj):
    if isinstance(obj, list):
        return [_build_ocorrencia_item(item.get('ocorrencia', {})) for item in obj]

    if not isinstance(obj, dict):
        raise ValueError(obj)

    ocorrencias = obj.get('ocorrencias')
    if isinstance(ocorrencias, dict):
        ocorrencia = ocorrencias.get('ocorrencia')
        if isinstance(ocorrencia, list):
            return [_build_ocorrencia_item(item) for item in ocorrencia]
        if isinstance(ocorrencia, dict):
            return [_build_ocorrencia_item(ocorrencia)]

    ocorrencia = obj.get('ocorrencia')
    if isinstance(ocorrencia, dict):
        return [_build_ocorrencia_item(ocorrencia)]
    if isinstance(ocorrencia, list):
        return [_build_ocorrencia_item(item) for item in ocorrencia]

    if isinstance(ocorrencias, list):
        return [_build_ocorrencia_item(item.get('ocorrencia', {})) for item in ocorrencias]

    raise ValueError(obj)


@register.filter('is_list')
def is_list(
        value):
    if type(value) is list:
        return True
    return False


@register.filter('finditem')
def finditem(
        obj,
        key):
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for value in obj.values():
            item = finditem(value, key)
            if item is not None:
                return item
        return None

    if isinstance(obj, list):
        for item in obj:
            finditem(item, key)
    return None


@register.filter('read_ocorrencias')
def read_ocorrencias(
        string):
    obj = json.loads(string or '{}')
    return _normalize_ocorrencias(obj)


@register.filter('read_ocorrencias_lote')
def read_ocorrencias_lote(
        string):
    lista = []
    obj = string or {}
    if isinstance(obj.get('ocorrencia'), list):
        for o in obj.get('ocorrencia', []):
            lista.append(
                {
                    'tipo': o.get('tipo'),
                    'codigo': o.get('codigo'),
                    'descricao': o.get('descricao'),
                    'localizacao': o.get('localizacao')
                })
    else:
        lista.append(
            {
                'tipo': obj.get('ocorrencia', {}).get('tipo'),
                'codigo': obj.get('ocorrencia', {}).get('codigo'),
                'descricao': obj.get('ocorrencia', {}).get('descricao'),
                'localizacao': obj.get('ocorrencia', {}).get('localizacao')
            })
    return lista


@register.filter('get_tipo_erro')
def get_tipo_erro(
        string):
    if int(string) == 1:
        return 'ERRO'
    else:
        return 'ADVERTÊNCIA'


@register.filter('to_json')
def to_json(
        string):
    try:
        return json.loads(string)
    except json.JSONDecodeError as e:
        logger.error("Failed to decode JSON: %s", e)
        return ''
    except Exception as e:
        logger.error("Unexpected error while processing JSON: %s", e)
        return ''


@register.filter('is_form_exists')
def is_form_exists(
        obj):
    file_path = Path(
        os.path.join(
            str(BASE_DIR),
            'apps',
            'esocial',
            'templates',
            obj.versao,
            f'{obj.evento}.html'))

    if file_path.is_file():
        return True
    return False


@register.filter('get_event_form')
def get_event_form(
        obj):
    return "{}/{}.html".format(obj.versao, obj.evento)


@register.filter('disabled')
def disabled(
        obj):
    if not obj.is_aberto:
        return 'disabled="disabled"'
    return ""


@register.filter('test')
def test(
        obj):
    try:
        logger.info(obj.__dict__)
    except Exception as e:
        logger.error("Failed to access __dict__ attribute of object: %s", e)
    return ''


@register.filter(name='readjson')
def readjson(
        json_string,
        arg):
    import json
    if not json_string:
        json_string = ''
    if not isinstance(json_string, str):
        json_string = json.dumps(json_string)
    if json_string:
        json_obj = json.loads(json_string)  # noqa: F841
        logger.info(json_obj)
        arg = "['%s']" % arg.replace(".", "']['")
        try:
            return eval('json_obj' + arg)
        except KeyError:
            return ''
    else:
        return ''


@register.filter('render_with_model_dict')
def render_with_model_dict(
        var,
        model):
    #
    # usage example {{ var|render_with_dict:model }}
    #
    if var:
        model_dict = model.__dict__
        return var % model_dict
    else:
        return ''


@register.filter('to_sql')
def to_sql(
        value):
    return value.replace("'", "''")


@register.filter('to_list')
def to_list(
        value):
    return value.split(',')


@register.filter(name='data_en_to_br')
def data_en_to_br(
        value):
    value = value.replace("/", "-")
    v = value.split('-')
    return v[2] + '/' + v[1] + '/' + v[0]


@register.filter(name='is_int')
def is_int(
        value):
    try:
        int(value)
        return True
    except ValueError as e:
        logger.error("Failed to convert value to int: %s", e)
        return False


@register.filter(name='multiply')
def multiply(
        value,
        arg):
    return value * arg


@register.filter(name='underline_to_hyphen')
def underline_to_hyphen(
        value):
    return value.replace("_", "-")


@register.filter(name='format_number_2dec_xml_reinf')
def format_number_2dec_xml_reinf(
        value):
    return str(value).replace('.', ',')


@register.filter(name='format_number_4dec_xml_reinf')
def format_number_4dec_xml_reinf(
        value):
    return str(value).replace('.', ',')


@register.filter(name='replace_aspas')
def replace_aspas(
        value):
    if not value:
        value = ''
    return value.replace("'", '"')


@register.filter(name='format_number_2dec_xml')
def format_number_2dec_xml(
        value):
    return "{:0.2f}".format(value)


@register.filter(name='format_number_4dec_xml')
def format_number_4dec_xml(
        value):
    return "{:0.4f}".format(value)


@register.filter(name='inteiro_xml')
def inteiro_xml(
        value):
    return str(int(value))


@register.filter(name='query')
def query(
        qs,
        **kwargs):
    """ template tag which allows queryset filtering. Usage:
          {% query books author=author as mybooks %}
          {% for book in mybooks %}
            ...
          {% endfor %}
    """
    return qs.filter(**kwargs)


@register.filter(name='to_xml')
def to_xml(
        texto):
    try:
        texto = texto.replace(">", '&gt;')
        texto = texto.replace("<", '&lt;')
        texto = texto.replace("&", '&amp;')
        texto = texto.replace('"', '&quot;')
        texto = texto.replace("'", '&apos;')
    except Exception as e:
        logger.error("Error converting text to XML-safe format: %s", e)
        return ''  # Return an empty string if conversion fails
    return texto


@register.filter(name='dec_to_int')
def dec_to_int(
        var):
    return int(var)


@register.filter(name='valor')
def valor(
        var):
    a = str(var).replace('.', '')
    return a


@register.filter(name='to_str')
def to_str(
        var):
    a = str(var)
    return a


@register.filter('json_tab')
def json_tab(
        json_str,
        variavel):
    if json_str == '{}':
        json_str = json_str.replace('}', '"tab": "%s"}' % variavel)
    else:
        json_str = json_str.replace('}', ', "tab": "%s"}' % variavel)
    return json_str


@register.filter('json_return_page')
def json_return_page(
        json_str,
        variavel):
    if json_str == '{}':
        json_str = json_str.replace('}', '"return_page": "%s"}' % variavel)
    else:
        json_str = json_str.replace('}', ', "return_page": "%s"}' % variavel)
    return json_str


@register.filter('json_return_hash')
def json_return_hash(
        json_str,
        variavel):
    if json_str == '{}':
        json_str = json_str.replace('}', '"return_hash": "%s"}' % variavel)
    else:
        json_str = json_str.replace('}', ', "return_hash": "%s"}' % variavel)
    return json_str


@register.filter('json_id')
def json_id(
        json_str,
        variavel):
    if json_str == '{}':
        json_str = json_str.replace('}', '"id": "%s"}' % variavel)
    else:
        json_str = json_str.replace('}', ', "id": "%s"}' % variavel)
    return json_str


@register.filter('json_print')
def json_print(
        json_str,
        variavel):
    if json_str == '{}':
        json_str = json_str.replace('}', '"print": "%s"}' % variavel)
    else:
        json_str = json_str.replace('}', ', "print": "%s"}' % variavel)
    return json_str


def dv_maker(
        v):
    if v >= 2:
        return 11 - v
    return 0


DV_maker = dv_maker


@register.filter(name='validate_CPF')
def validate_cpf(
        value):
    """
    Value can be either a string in the format XXX.XXX.XXX-XX or an
    11-digit number.
    """
    value = value.replace('.', '').replace('-', '')
    if value in EMPTY_VALUES:
        return False
    if not value.isdigit():
        value = re.sub(r"[-\.]", "", value)
    try:
        int(value)
    except ValueError:
        return False
    if len(value) != 11:
        return False
    orig_dv = value[-2:]

    new_1dv = sum(
        [i * int(value[idx])
         for idx, i in enumerate(range(10, 1, -1))])
    new_1dv = dv_maker(new_1dv % 11)
    value = value[:-2] + str(new_1dv) + value[-1]
    new_2dv = sum(
        [i * int(value[idx])
         for idx, i in enumerate(range(11, 1, -1))])
    new_2dv = dv_maker(new_2dv % 11)
    value = value[:-1] + str(new_2dv)
    if value[-2:] != orig_dv:
        return False
    return True


validate_CPF = validate_cpf


@register.filter('addstr')
def addstr(
        arg1,
        arg2):
    # concatenate arg1 & arg2
    return str(arg1) + str(arg2)


@register.filter('add')
def add(
        arg1,
        arg2):
    # concatenate arg1 & arg2
    return str(arg1) + '|' + str(arg2)


@register.filter('get_permissao')
def get_permissao(
        dict,
        key):
    try:
        if dict[str(key)] == 0:
            return False
        if dict[str(key)] == 1:
            return True
    except Exception as e:
        logger.error("Error accessing permission with key '%s': %s", key, e)
    return False


@register.filter('divide')
def divide(
        value,
        arg):
    if not arg:
        arg = 0
    if not value:
        value = 0
    quant_total = (arg * 100.00)
    if int(quant_total) == 0:
        quant_total = 1
    quant_nao_enviado = (value * 100.00)
    quant_enviado = quant_total - quant_nao_enviado
    divide = (quant_enviado / quant_total) * 100
    return int(divide)


@register.filter('base64_encode_me')
def base64_encode_me(
        text):
    import base64
    encode_to_url = base64.urlsafe_b64encode(text)
    return encode_to_url


@register.filter('get_value_from_dict')
def get_value_from_dict(
        dict_data,
        key):
    """
    Usage example: {{ your_dict|get_value_from_dict:your_key }}
    """
    if key:
        a = dict_data.get(key)
        try:
            a = int(a)
        except Exception as e:
            logger.error("Error converting value for key '%s' to int: %s", key, e)
        if not a:
            a = ''
        return a
    return ''


@register.filter(name='addcss')
def addcss(
        value,
        arg):
    return value.as_widget(attrs={'class': arg})


@register.filter(name='addcss_select2')
def addcss_select2(
        value,
        arg):
    return value.as_widget(attrs={'class': arg, 'style': 'width: 100%'})


@register.filter(name='notNone')
def not_none(
        var):
    a = ''
    if var:
        a = var
    return a


notNone = not_none


@register.filter(name='mes_ano')
def mes_ano(
        var):
    mes = var[4:7]
    ano = var[2:4]
    if mes == '01':
        mes = 'Jan/'
    if mes == '02':
        mes = 'Fev/'
    if mes == '03':
        mes = 'Mar/'
    if mes == '04':
        mes = 'Abr/'
    if mes == '05':
        mes = 'Mai/'
    if mes == '06':
        mes = 'Jun/'
    if mes == '07':
        mes = 'Jul/'
    if mes == '08':
        mes = 'Ago/'
    if mes == '09':
        mes = 'Set/'
    if mes == '10':
        mes = 'Out/'
    if mes == '11':
        mes = 'Nov/'
    if mes == '12':
        mes = 'Dez/'
    return mes + ano


@register.filter(name='ano_mes_extenso')
def ano_mes_extenso(
        value):
    a = value.split('-')
    ano = a[0]
    mes = a[1]
    if mes == '01':
        mes_extenso = 'Janeiro'
    elif mes == '02':
        mes_extenso = 'Fevereiro'
    elif mes == '03':
        mes_extenso = 'Março'
    elif mes == '04':
        mes_extenso = 'Abril'
    elif mes == '05':
        mes_extenso = 'Maio'
    elif mes == '06':
        mes_extenso = 'Junho'
    elif mes == '07':
        mes_extenso = 'Julho'
    elif mes == '08':
        mes_extenso = 'Agosto'
    elif mes == '09':
        mes_extenso = 'Setembro'
    elif mes == '10':
        mes_extenso = 'Outubro'
    elif mes == '11':
        mes_extenso = 'Novembro'
    elif mes == '12':
        mes_extenso = 'Dezembro'
    return mes_extenso + '/' + ano


@register.filter(name='inteiro')
def inteiro(
        var):
    a = str(var).split('.')
    b = a[0]
    return int(b)


@register.filter(name='padrao_americano')
def padrao_americano(
        var):
    return str(var)


@register.filter(name='total_quant')
def total_quant(
        list,
        arg):
    soma = sum(d[arg] for d in list)
    return soma


@register.filter(name='percentage')
def percentage(
        fraction,
        population):
    # Example: {{ yes.count|percentage:votes.count }} votes.count - total ||| yes.count - parcial
    try:
        return "%.2f%%" % ((float(fraction) / float(population)) * 100)
    except ValueError:
        return ''
