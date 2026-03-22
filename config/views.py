import os

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import Http404, HttpResponse
from django.views import View
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response

from apps.esocial.models import (
    Certificados as CertificadosEsocial,
    Transmissor as TransmissorEsocial,
)
from config.settings import ADMINS, EMAIL_HOST_USER


@login_required
def send_test_email(
        request):
    send_mail(
        'Teste de Envio de E-mail',
        'Este é um e-mail de teste enviado pelo Django usando Gmail SMTP.',
        EMAIL_HOST_USER,  # E-mail de origem
        [a[1] for a in ADMINS],  # E-mail de destino
        fail_silently=False,
    )
    return HttpResponse("E-mail enviado com sucesso!")


class Error500TestView(View):
    def get(
            self,
            request):
        # Lança uma exceção para simular um erro 500
        raise ValueError("Este é um erro simulado para testar o envio de emails de erro.")


class CustomAuthToken(ObtainAuthToken):

    def post(
            self,
            request,
            *args,
            **kwargs):
        from django.db.models import Q
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)

        if user.is_superuser:
            certificados_esocial = CertificadosEsocial.all_objects. \
                values('id', 'nome')
            transmissores_esocial = TransmissorEsocial.all_objects. \
                values('id', 'nome_empresa', 'tpinsc', 'nrinsc')
        else:
            certificados_esocial = CertificadosEsocial.all_objects. \
                filter(Q(created_by_id=user.id) | Q(users__id=user.id)). \
                values('id', 'nome')
            transmissores_esocial = TransmissorEsocial.all_objects. \
                filter(Q(created_by_id=user.id) | Q(users__id=user.id)). \
                values('id', 'nome_empresa', 'tpinsc', 'nrinsc')

        return Response(
            {
                'token': token.key,
                'user_id': user.pk,
                'esocial': {
                    'certificados': certificados_esocial,
                    'transmissores': transmissores_esocial,
                },
            })


@login_required
def download_media(request, file_path):
    """
    View para download de arquivos de mídia.
    Apenas usuários autenticados podem acessar os arquivos.
    """
    # Normaliza o caminho do arquivo
    full_path = os.path.normpath(os.path.join(settings.MEDIA_ROOT, file_path))

    # Verifica se o caminho está dentro do diretório MEDIA_ROOT
    if not full_path.startswith(os.path.abspath(settings.MEDIA_ROOT)):
        raise Http404("Arquivo não encontrado.")

    # Verifica se o arquivo existe
    if not os.path.isfile(full_path):
        raise Http404("Arquivo não encontrado.")

    # Lê o conteúdo do arquivo
    with open(full_path, 'rb') as file:
        response = HttpResponse(file.read(), content_type="application/octet-stream")
        response[
            'Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
        return response
