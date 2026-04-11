import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Cria ou atualiza o superusuário padrão se ainda não houver um superusuário."

    def handle(self, *args, **options):
        user_model = get_user_model()

        if user_model.objects.filter(is_superuser=True).exists():
            logger.info("Já existe um superusuário cadastrado.")
            return

        username = settings.SUPERUSER_USERNAME.strip()
        email = settings.SUPERUSER_EMAIL.strip()

        user, created = user_model.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_active": True,
                "is_staff": True,
                "is_superuser": True,
            },
        )

        user.email = email
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.set_password(settings.SUPERUSER_PASSWORD)
        user.save()

        if created:
            logger.info("Superusuário padrão criado com sucesso.")
        else:
            logger.info("Usuário existente promovido a superusuário com sucesso.")
