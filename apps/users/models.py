import re

import unicodedata
from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.db.models import CharField
from multiselectfield import MultiSelectField

from apps.esocial.choices import EVENTOS


def remover_acentos_caracteres_especiais(
        palavra):
    # Unicode normalize transforma um caracter em seu equivalente em latin.
    nfkd = unicodedata.normalize('NFKD', palavra)
    palavra_sem_acento = u"".join([c for c in nfkd if not unicodedata.combining(c)])

    # Usa expressão regular para retornar a palavra apenas com números, letras e espaço
    return re.sub(r'[^a-zA-Z0-9 ]', '', palavra_sem_acento)


class User(AbstractUser):
    cols = {
        'name': 4,
        'eventos': 12,
    }

    username = models.CharField(
        'Nome do usuário',
        max_length=50,
        unique=True,
        help_text='Obrigatório. Informe o nome do usuário.',
    )

    name = CharField("Nome Completo", blank=True, max_length=255)

    eventos = MultiSelectField(
        "Eventos", choices=EVENTOS, null=True, blank=True)

    is_staff = models.BooleanField(
        "Acessa o sistema?",
        default=False,
        help_text='Designates whether the user can log into this admin site.',
    )
    is_active = models.BooleanField(
        "Está ativo?",
        default=True,
        help_text=(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )

    is_superuser = models.BooleanField(
        "É administrador?",
        default=False,
        help_text=(
            'Designates that this user has all permissions without '
            'explicitly assigning them.'
        ),
    )
    groups = models.ManyToManyField(
        Group,
        verbose_name="Grupos",
        blank=True,
        help_text=(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="user_set",
        related_query_name="user",
    )

    user_str = models.CharField(
        'User String',
        blank=True, null=True, max_length=200, )

    user_search_str = models.CharField(
        'User Search String',
        blank=True, null=True, max_length=200, )

    def _get_name_parts(self):
        if ' ' in self.name:
            return self.name.split(' ')
        return [self.name, self.name]

    def _update_name_fields(self):
        name_parts = self._get_name_parts()
        if not self.first_name:
            self.first_name = name_parts[0]
        if not self.last_name:
            self.last_name = name_parts[-1]

    def _build_user_str(self):
        return '{:08n} {} {} ({})'.format(
            self.pk,
            self.first_name or "",
            self.last_name or "",
            self.username or "",
        )

    def _update_search_fields(self):
        self.user_str = self._build_user_str()
        self.user_search_str = '{} {}'.format(
            self.username,
            remover_acentos_caracteres_especiais(self.user_str),
        )

    def save(
            self,
            force_insert=False,
            force_update=False,
            using=None,
            update_fields=None):
        if self.name:
            self._update_name_fields()
        if self.pk:
            self._update_search_fields()

        super(User, self).save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )
        if not self.user_str:
            self._update_search_fields()
            super(User, self).save(
                using=using,
                update_fields=['user_str', 'user_search_str'],
            )

    def nome(self):
        return f'{self.first_name} {self.last_name}'

    def __str__(
            self):
        if self.first_name and self.last_name:
            return f'{self.first_name} {self.last_name}'
        else:
            return self.username

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
