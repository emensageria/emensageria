import base64
import os
from typing import Any

from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.storage import FileSystemStorage
from django.db import models

from config.mixins import BaseModelEsocial

User = get_user_model()


def get_cipher():
    """Retorna uma instância de Fernet para criptografia/descriptografia."""
    return Fernet(settings.CRYPTO_KEY.encode())


class Certificados(BaseModelEsocial):
    cols = {
        'nome': 12,
        'certificado': 12,
        'senha': 12,
        'users': 12,
        'created_at': 3,
        'created_by': 3,
        'updated_at': 3,
        'updated_by': 3,
    }
    nome = models.CharField('Nome', max_length=300, )
    fs_certificado = FileSystemStorage(location=os.path.join(settings.BASE_DIR, settings.CERT_PATH))
    certificado = models.FileField('Arquivo', storage=fs_certificado)
    senha_certificado = models.TextField(
        "Senha do certificado criptografada", blank=True)
    users: models.ManyToManyField = models.ManyToManyField(
        User, verbose_name='Usuários', related_name='esocial_crt_users', blank=True,
        help_text="Informe a lista de usuários que tem acesso a utilizar este certificado.")

    _senha_certificado_input: Any = None

    def get_senha(
            self):
        return self.get_senha_certificado()

    def cert_host(
            self):
        return os.path.join(settings.BASE_DIR, settings.CERT_PATH, self.certificado.name)

    def save(
            self,
            *args,
            **kwargs):
        # A senha será criptografada apenas se um novo valor for fornecido
        if self._senha_certificado_input:
            self.senha_certificado = base64.urlsafe_b64encode(
                get_cipher().encrypt(self._senha_certificado_input.encode())
            ).decode()  # Criptografa e armazena em base64
        super().save(*args, **kwargs)

    def get_senha_certificado(
            self):
        """Descriptografa e retorna a senha do certificado."""
        if self.senha_certificado:
            try:
                return get_cipher().decrypt(
                    base64.urlsafe_b64decode(self.senha_certificado.encode())).decode()
            except Exception:
                return None
        return None

    def __str__(
            self):
        return self.nome

    class Meta:
        verbose_name = 'Certificados'
        verbose_name_plural = 'Certificados'
        ordering = [
            '-id', ]
