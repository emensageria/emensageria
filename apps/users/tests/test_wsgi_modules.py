import importlib
from unittest.mock import patch

from django.test import SimpleTestCase


class WsgiModulesTests(SimpleTestCase):

    def test_config_wsgi_sets_environment_and_builds_application(self):
        sentinel_app = object()
        with patch("django.core.wsgi.get_wsgi_application", return_value=sentinel_app), \
                patch("os.environ.setdefault") as setdefault_mock:
            module = importlib.reload(importlib.import_module("config.wsgi"))

        setdefault_mock.assert_called_with("DJANGO_SETTINGS_MODULE", "config.settings")
        self.assertIs(module.application, sentinel_app)

    def test_root_wsgi_sets_environment_and_builds_application(self):
        sentinel_app = object()
        with patch("django.core.wsgi.get_wsgi_application", return_value=sentinel_app), \
                patch("os.environ.setdefault") as setdefault_mock:
            module = importlib.reload(importlib.import_module("wsgi"))

        setdefault_mock.assert_called_with("DJANGO_SETTINGS_MODULE", "config.settings")
        self.assertIs(module.application, sentinel_app)
