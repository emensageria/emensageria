import re

from django.db import models

from apps.esocial.choices import TIPO_INSCRICAO
from apps.users.models import User
from config.mixins import BaseModelEsocial


class Transmissor(BaseModelEsocial):
    cols = {
        'transmissor_tpinsc': 6,
        'transmissor_nrinsc': 6,
        'nome_empresa': 6,
        'logotipo': 6,
        'endereco_completo': 12,
        'nrinsc': 6,
        'tpinsc': 6,
        'certificado': 12,
        'users': 12,
        'created_at': 3,
        'created_by': 3,
        'updated_at': 3,
        'updated_by': 3,
    }
    transmissor_tpinsc = models.IntegerField(
        'Tipo de inscrição do transmissor', choices=TIPO_INSCRICAO, )
    transmissor_nrinsc = models.CharField(
        'Número de inscrição do transmissor', max_length=15)
    nome_empresa = models.CharField(
        'Nome da empresa', max_length=200, unique=True)
    logotipo = models.FileField(
        'Logotipo', upload_to="logotipo",
        blank=True, null=True)
    endereco_completo = models.TextField(
        'Endereço', blank=True)
    tpinsc = models.IntegerField(
        'Tipo de inscrição do empregador', choices=TIPO_INSCRICAO, )
    nrinsc = models.CharField(
        'Número de inscrição do empregador', max_length=15, unique=True,
        help_text="O CNPJ completo somente pode ser utilizado por órgãos públicos, "
                  "os demais empregadores deverão informar somente o "
                  "CNPJ base (8 primeiros dígitos do CNPJ)")
    certificado = models.ForeignKey(
        'Certificados',
        on_delete=models.PROTECT,
        verbose_name='Certificado',
        related_name='%(class)s_certificado', )
    users = models.ManyToManyField(
        User, verbose_name='Usuários', related_name='transmissores_users', blank=True,
        help_text="Informe a lista de usuários que tem acesso a utilizar este transmissor."
    )  # type: ignore

    def __str__(
            self):
        return self.nome_empresa

    def save(
            self,
            force_insert=False,
            force_update=False,
            using=None,
            update_fields=None):
        self.transmissor_nrinsc = re.sub(r'\D', '', self.transmissor_nrinsc)
        self.nrinsc = re.sub(r'\D', '', self.nrinsc)
        super(Transmissor, self).save(
            force_insert=False,
            force_update=False,
            using=None,
            update_fields=None)

    class Meta:
        verbose_name = 'Transmissor'
        verbose_name_plural = 'Transmissor'
        ordering = [
            '-id', ]
