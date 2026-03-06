import os
import tempfile
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from django.test import RequestFactory, SimpleTestCase, override_settings

from config.views import CustomAuthToken, Error500TestView, download_media, send_test_email


class ViewsTests(SimpleTestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def test_send_test_email_when_authenticated_returns_success(self):
        request = self.factory.get("/enviar-email-teste/")
        request.user = SimpleNamespace(is_authenticated=True)

        with patch("config.views.send_mail") as send_mail_mock:
            response = send_test_email(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn("E-mail enviado com sucesso", response.content.decode())
        send_mail_mock.assert_called_once()

    def test_send_test_email_when_unauthenticated_redirects_to_login(self):
        request = self.factory.get("/enviar-email-teste/")
        request.user = AnonymousUser()

        response = send_test_email(request)
        self.assertEqual(response.status_code, 302)

    def test_error_500_test_view_raises_value_error(self):
        request = self.factory.get("/test-error/")
        with self.assertRaises(ValueError):
            Error500TestView().get(request)

    def test_custom_auth_token_post_for_superuser(self):
        user = SimpleNamespace(id=1, pk=1, is_superuser=True)
        serializer = MagicMock()
        serializer.validated_data = {"user": user}
        serializer_class = MagicMock(return_value=serializer)

        cert_manager = MagicMock()
        cert_manager.values.return_value = [{"id": 1, "nome": "Cert"}]
        trans_manager = MagicMock()
        trans_manager.values.return_value = [{"id": 2, "nome_empresa": "Empresa"}]

        request = SimpleNamespace(data={"username": "admin"})
        view = CustomAuthToken()
        view.serializer_class = serializer_class

        with patch(
            "config.views.Token.objects.get_or_create",
            return_value=(SimpleNamespace(key="t"), True),
        ), \
                patch("config.views.CertificadosEsocial.all_objects", cert_manager), \
                patch("config.views.TransmissorEsocial.all_objects", trans_manager):
            response = view.post(request)

        serializer_class.assert_called_once_with(data=request.data, context={"request": request})
        serializer.is_valid.assert_called_once_with(raise_exception=True)
        self.assertEqual(response.data["token"], "t")
        self.assertEqual(response.data["user_id"], 1)
        self.assertEqual(
            response.data["esocial"]["certificados"],
            [{"id": 1, "nome": "Cert"}],
        )
        self.assertEqual(
            response.data["esocial"]["transmissores"],
            [{"id": 2, "nome_empresa": "Empresa"}],
        )

    def test_custom_auth_token_post_for_regular_user(self):
        user = SimpleNamespace(id=9, pk=9, is_superuser=False)
        serializer = MagicMock()
        serializer.validated_data = {"user": user}
        serializer_class = MagicMock(return_value=serializer)

        cert_manager = MagicMock()
        cert_manager.filter.return_value.values.return_value = [{"id": 1, "nome": "Cert"}]
        trans_manager = MagicMock()
        trans_manager.filter.return_value.values.return_value = [
            {"id": 2, "nome_empresa": "Empresa"}
        ]

        request = SimpleNamespace(data={"username": "regular"})
        view = CustomAuthToken()
        view.serializer_class = serializer_class

        with patch(
            "config.views.Token.objects.get_or_create",
            return_value=(SimpleNamespace(key="tok"), True),
        ), \
                patch("config.views.CertificadosEsocial.all_objects", cert_manager), \
                patch("config.views.TransmissorEsocial.all_objects", trans_manager):
            response = view.post(request)

        self.assertEqual(response.data["token"], "tok")
        self.assertEqual(response.data["user_id"], 9)
        cert_manager.filter.assert_called_once()
        trans_manager.filter.assert_called_once()

    def test_download_media_returns_file_for_authenticated_user(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "arquivo.txt")
            with open(file_path, "wb") as file:
                file.write(b"conteudo")

            request = self.factory.get("/media/arquivo.txt")
            request.user = SimpleNamespace(is_authenticated=True)

            with override_settings(MEDIA_ROOT=tmpdir):
                response = download_media(request, "arquivo.txt")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"conteudo")
        self.assertEqual(response["Content-Disposition"], 'attachment; filename="arquivo.txt"')

    def test_download_media_raises_404_for_path_traversal(self):
        request = self.factory.get("/media/invalido")
        request.user = SimpleNamespace(is_authenticated=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            with override_settings(MEDIA_ROOT=tmpdir):
                with self.assertRaises(Http404):
                    download_media(request, "../segredo.txt")

    def test_download_media_raises_404_when_file_does_not_exist(self):
        request = self.factory.get("/media/inexistente")
        request.user = SimpleNamespace(is_authenticated=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            with override_settings(MEDIA_ROOT=tmpdir):
                with self.assertRaises(Http404):
                    download_media(request, "nao_existe.txt")
