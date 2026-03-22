import os
from datetime import datetime
from django.core.management.base import BaseCommand
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend
from apps.esocial.models import Certificados


class Command(BaseCommand):
    help = 'Verifica a validade de todos os certificados PKCS#12 (.pfx) no modelo Certificados.'

    def handle(self, *args, **kwargs):
        self.stdout.write('Iniciando verificação de certificados...')

        certificados = Certificados.objects.all()
        if not certificados.exists():
            self.stdout.write(self.style.WARNING('Nenhum certificado encontrado.'))
            return

        for cert in certificados:
            cert_path = cert.cert_host()

            # Verifica se o arquivo do certificado existe
            if not os.path.exists(cert_path):
                self.stdout.write(
                    self.style.ERROR(f'O arquivo do certificado "{cert.nome}" não foi '
                                     F'encontrado: {cert_path}')
                )
                continue

            # Carregar o arquivo PKCS#12 (.pfx)
            with open(cert_path, 'rb') as f:
                pkcs12_data = f.read()

            password = cert.get_senha_certificado()
            if password is not None:
                password = password.encode('utf-8')
            _private_key, certificate, _additional_certs = pkcs12.load_key_and_certificates(
                pkcs12_data,
                password=password,
                backend=default_backend()
            )

            if not certificate:
                raise ValueError(f'O certificado "{cert.nome}" está vazio ou inválido.')

            # Extrair informações do certificado
            validade_inicio = certificate.not_valid_before
            validade_fim = certificate.not_valid_after
            agora = datetime.now()

            # Verificar datas de validade
            if validade_inicio <= agora <= validade_fim:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Certificado "{cert.nome}" está válido. '
                        f'Válido de {validade_inicio} até {validade_fim}.'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'Certificado "{cert.nome}" expirado ou inválido. '
                        f'Válido de {validade_inicio} até {validade_fim}.'
                    )
                )
        self.stdout.write(self.style.SUCCESS('Verificação de certificados concluída.'))
