from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from reportlab.lib import utils
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from apps.esocial.models import Eventos


def get_size_image(
        path):
    img = utils.ImageReader(path)
    return img.getSize()


def generate_text_list(
        texto,
        compr):
    lista = []
    palavras = texto.split(' ')
    if not palavras:
        return lista

    novo_texto = palavras[0]
    for palavra in palavras[1:]:
        if len(novo_texto) + len(palavra) + 1 > compr:
            lista.append(novo_texto)
            novo_texto = palavra
        else:
            novo_texto += ' ' + palavra
    lista.append(novo_texto)
    return lista


def draw_logo(
        my_canvas,
        evento,
        settings):
    if not evento.lote or not evento.lote.transmissor.logotipo:
        return

    import os

    logo = os.path.join(
        settings.BASE_DIR,
        settings.MEDIA_ROOT,
        evento.lote.transmissor.logotipo.file.name)
    logo_w, logo_h = get_size_image(logo)
    my_canvas.drawImage(
        logo,
        159 * mm,
        280 * mm,
        width=30 * mm,
        height=(logo_h / logo_w) * 30 * mm,
    )


def draw_transmissor_endereco(
        my_canvas,
        evento):
    if not evento.lote or not evento.lote.transmissor.logotipo:
        return

    my_canvas.setFont('Helvetica', 8)
    endereco_completo = evento.lote.transmissor.endereco_completo.replace('\r', '')
    linha_inicial = 16
    for endereco in endereco_completo.split('\n'):
        my_canvas.drawString(20 * mm, linha_inicial * mm, endereco)
        linha_inicial -= 4


def draw_evento_cabecalho(
        my_canvas,
        evento):
    my_canvas.setFont('Helvetica', 12)
    my_canvas.drawString(20 * mm, 280 * mm, evento.get_evento_display())
    my_canvas.setFont('Helvetica', 9)
    my_canvas.drawString(22 * mm, 252 * mm, evento.identidade)
    my_canvas.drawString(108 * mm, 252 * mm, evento.versao)
    my_canvas.drawString(150 * mm, 252 * mm, evento.get_tpamb_display())
    my_canvas.drawString(22 * mm, 233 * mm, evento.get_procemi_display())
    my_canvas.drawString(79 * mm, 233 * mm, evento.verproc)
    my_canvas.drawString(108 * mm, 233 * mm, evento.get_tpinsc_display())
    my_canvas.drawString(136 * mm, 233 * mm, evento.nrinsc)


def draw_recepcao_envio(
        my_canvas,
        retorno_envio,
        retorno_consulta):
    if not (retorno_envio.get('dadosRecepcaoLote') or retorno_envio.get('status')):
        return

    recepcao = retorno_envio.get('dadosRecepcaoLote')
    status = retorno_envio.get('status') or {}
    if recepcao:
        my_canvas.drawString(22 * mm, 214 * mm, recepcao.get('tpAmb') or '')
        my_canvas.setFont('Helvetica', 9)
        my_canvas.drawString(50 * mm, 214 * mm, recepcao.get('dhRecepcao') or '')
        my_canvas.drawString(94 * mm, 214 * mm, recepcao.get('versaoAplicativoRecepcao') or '')
        my_canvas.drawString(122 * mm, 214 * mm, recepcao.get('protocoloEnvio') or '')
    if not retorno_consulta:
        my_canvas.drawString(22 * mm, 195 * mm, status.get('cdResposta') or '')
        my_canvas.drawString(36 * mm, 195 * mm, status.get('descResposta') or '')


def draw_recepcao_consulta(
        my_canvas,
        retorno_consulta):
    recepcao = retorno_consulta.get('recepcao')
    if recepcao:
        my_canvas.drawString(22 * mm, 214 * mm, recepcao.get('tpAmb') or '')


def draw_ocorrencias(
        my_canvas,
        ocorrencias):
    if not ocorrencias:
        my_canvas.drawString(22 * mm, 160 * mm, 'Não há')
        return

    if not isinstance(ocorrencias, list):
        ocorrencias = [ocorrencias]

    linha_inicial = 160
    for ocorrencia in ocorrencias:
        my_canvas.drawString(22 * mm, linha_inicial * mm, ocorrencia.get('tipo') or '')
        my_canvas.drawString(32 * mm, linha_inicial * mm, ocorrencia.get('codigo') or '')
        descricao = (ocorrencia.get('descricao') or '').replace('\n', ' ')
        for descricao_linha in generate_text_list(descricao, 88):
            my_canvas.drawString(42 * mm, linha_inicial * mm, descricao_linha)
            linha_inicial -= 5
        localizacao = ocorrencia.get('localizacao') or ''
        if localizacao:
            my_canvas.drawString(42 * mm, linha_inicial * mm, localizacao)
        else:
            linha_inicial += 5
        linha_inicial -= 7


def draw_processamento(
        my_canvas,
        retorno_consulta):
    processamento = retorno_consulta.get('processamento')
    if not processamento:
        return

    my_canvas.drawString(22 * mm, 195 * mm, processamento.get('cdResposta') or '')
    my_canvas.drawString(36 * mm, 195 * mm, processamento.get('descResposta') or '')
    my_canvas.drawString(122 * mm, 195 * mm, processamento.get('versaoAppProcessamento') or '')
    my_canvas.drawString(150 * mm, 195 * mm, processamento.get('dhProcessamento') or '')

    recibo = retorno_consulta.get('recibo')
    if recibo:
        my_canvas.drawString(22 * mm, 176 * mm, recibo.get('nrRecibo') or '')
        my_canvas.drawString(79 * mm, 176 * mm, recibo.get('hash') or '')

    ocorrencias = (processamento.get('ocorrencias') or {}).get('ocorrencia')
    draw_ocorrencias(my_canvas, ocorrencias)


def pdf_recibo_evento(
        evento):
    import os
    from config import settings
    from config.functions import create_dir

    background = os.path.join(settings.BASE_DIR, 'staticfiles', 'recibo', 'recibo_evento.jpg')
    create_dir(evento.pdf_file())

    my_canvas = canvas.Canvas(
        evento.pdf_file(),
        pagesize=A4)
    my_canvas.setTitle(f"Recibo do Evento - {evento.identidade}")
    my_canvas.drawImage(
        background,
        0 * mm, 0 * mm,
        width=210 * mm,
        height=297 * mm, mask='auto')
    draw_logo(my_canvas, evento, settings)
    draw_transmissor_endereco(my_canvas, evento)
    draw_evento_cabecalho(my_canvas, evento)

    # RECEPÇÃO
    re = evento.retorno_envio_lote_json
    co = evento.retorno_consulta_json
    draw_recepcao_envio(my_canvas, re, co)

    # RECEPÇÃO
    draw_recepcao_consulta(my_canvas, co)

    # PROCESSAMENTO
    draw_processamento(my_canvas, co)
    my_canvas.save()


@login_required
def eventos_recibo(
        request,
        pk):
    evento = get_object_or_404(Eventos, id=pk)
    pdf_recibo_evento(evento)
    with open(evento.pdf_file(), 'rb') as fh:
        response = HttpResponse(fh.read(), content_type="application/pdf")
        response['Content-Disposition'] = f'inline; filename={evento.identidade}.pdf'
        response['Content-Title'] = f'Recibo do Evento - {evento.identidade}'
        return response
