import importlib
import os
import sys

from django.test import SimpleTestCase

import config.settings as settings_module


class SettingsModuleTests(SimpleTestCase):

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        with cls.settings_reload_context(["manage.py", "test"], {"ESOCIAL_TPAMB": "2"}):
            importlib.reload(settings_module)

    @classmethod
    def settings_reload_context(cls, argv, env_vars):
        return _ReloadContext(argv=argv, env_vars=env_vars)

    def test_parse_admins_returns_empty_list_when_value_is_empty(self):
        self.assertEqual(settings_module.parse_admins(""), [])
        self.assertEqual(settings_module.parse_admins(None), [])

    def test_parse_admins_splits_and_strips_values(self):
        parsed = settings_module.parse_admins("Nome Um,um@email.com; Nome Dois,dois@email.com;")
        self.assertEqual(parsed[0], ("Nome Um", "um@email.com"))
        self.assertEqual(parsed[1], ("Nome Dois", "dois@email.com"))

    def test_reload_settings_without_test_command_keeps_default_database(self):
        with self.settings_reload_context(["manage.py", "runserver"], {"ESOCIAL_TPAMB": "2"}):
            reloaded = importlib.reload(settings_module)

        self.assertNotEqual(reloaded.DATABASES["default"]["NAME"], ":memory:")

    def test_reload_settings_with_tpamb_production_sets_target_production(self):
        with self.settings_reload_context(["manage.py", "runserver"], {"ESOCIAL_TPAMB": "1"}):
            reloaded = importlib.reload(settings_module)

        self.assertEqual(reloaded.ESOCIAL_TARGET, "production")


class _ReloadContext:

    def __init__(self, argv, env_vars):
        self.argv = argv
        self.env_vars = env_vars
        self.original_argv = None
        self.original_env = {}

    def __enter__(self):
        self.original_argv = list(sys.argv)
        sys.argv = list(self.argv)

        for key, value in self.env_vars.items():
            self.original_env[key] = os.environ.get(key)
            os.environ[key] = value

    def __exit__(self, exc_type, exc, tb):
        sys.argv = self.original_argv
        for key, old_value in self.original_env.items():
            if old_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old_value
