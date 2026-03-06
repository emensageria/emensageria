import runpy
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase


class GenerateFernetKeyTests(SimpleTestCase):

    def test_generate_and_save_key_returns_when_env_file_does_not_exist(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"

            with patch("config.generate_fernet_key.Path", return_value=env_file), \
                    patch("config.generate_fernet_key.Fernet.generate_key", return_value=b"k"), \
                    patch("builtins.print") as print_mock:
                from config.generate_fernet_key import generate_and_save_key
                generate_and_save_key()

            print_mock.assert_called_once()
            self.assertIn("não foi encontrado", print_mock.call_args[0][0].lower())

    def test_generate_and_save_key_updates_existing_crypto_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("CRYPTO_KEY=old\nDEBUG=1\n", encoding="utf-8")

            with patch("config.generate_fernet_key.Path", return_value=env_file):
                with patch(
                    "config.generate_fernet_key.Fernet.generate_key",
                    return_value=b"newkey",
                ):
                    with patch("builtins.print"):
                        from config.generate_fernet_key import generate_and_save_key
                        generate_and_save_key()

            content = env_file.read_text(encoding="utf-8")
            self.assertIn("CRYPTO_KEY=newkey", content)
            self.assertEqual(content.count("CRYPTO_KEY="), 1)

    def test_generate_and_save_key_appends_crypto_key_when_absent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("DEBUG=1\n", encoding="utf-8")

            with patch("config.generate_fernet_key.Path", return_value=env_file):
                with patch(
                    "config.generate_fernet_key.Fernet.generate_key",
                    return_value=b"append",
                ):
                    with patch("builtins.print"):
                        from config.generate_fernet_key import generate_and_save_key
                        generate_and_save_key()

            content = env_file.read_text(encoding="utf-8")
            self.assertIn("DEBUG=1", content)
            self.assertIn("CRYPTO_KEY=append", content)

    def test_module_main_executes_generate_function(self):
        sys.modules.pop("config.generate_fernet_key", None)
        with patch("pathlib.Path.exists", return_value=False), \
                patch("cryptography.fernet.Fernet.generate_key", return_value=b"x"), \
                patch("builtins.print") as print_mock:
            runpy.run_module("config.generate_fernet_key", run_name="__main__")

        print_mock.assert_called()
