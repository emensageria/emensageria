import os
import tempfile
from unittest.mock import MagicMock, mock_open, patch

from django.test import SimpleTestCase
from lxml import etree

from config import functions


class FunctionsModuleTests(SimpleTestCase):

    def test_verify_domain_parses_referer_and_delegates_validation(self):
        with patch(
            "config.functions.url_has_allowed_host_and_scheme",
            return_value=True,
        ) as validator:
            result = functions.verify_domain("https://example.com:8443/path")

        validator.assert_called_once_with(
            "example.com",
            allowed_hosts=functions.ALLOWED_HOSTS,
        )
        self.assertTrue(result)

    def test_verify_domain_handles_empty_referer(self):
        with patch(
            "config.functions.url_has_allowed_host_and_scheme",
            return_value=False,
        ) as validator:
            result = functions.verify_domain(None)

        validator.assert_called_once_with("", allowed_hosts=functions.ALLOWED_HOSTS)
        self.assertFalse(result)

    def test_create_dir_creates_missing_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "nested", "arquivo.txt")
            functions.create_dir(filename)
            self.assertTrue(os.path.isdir(os.path.dirname(filename)))

    def test_create_dir_raises_when_directory_is_still_missing(self):
        with patch("config.functions.os.path.dirname", return_value="/tmp/inexistente"), \
                patch("config.functions.os.path.exists", side_effect=[False, False]), \
                patch("config.functions.os.makedirs"):
            with self.assertRaises(NameError):
                functions.create_dir("/tmp/inexistente/arquivo.txt")

    def test_save_file_writes_content(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "saida", "file.txt")
            functions.save_file(filename, "conteudo")
            self.assertEqual(functions.read_file(filename), "conteudo")

    def test_save_file_raises_when_file_not_created(self):
        with patch("config.functions.create_dir"), \
                patch("config.functions.codecs.open", mock_open()), \
                patch("config.functions.os.path.exists", return_value=False):
            with self.assertRaises(NameError):
                functions.save_file("/tmp/arq.txt", "x")

    def test_read_file_raises_when_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "inexistente.txt")
            with self.assertRaises(NameError):
                functions.read_file(filename)

    def test_validar_schema_returns_parse_error_when_xml_is_invalid(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as tmp_xml:
            tmp_xml.write("<raiz>")
            tmp_xml_path = tmp_xml.name

        try:
            result = functions.validar_schema("qualquer.xsd", tmp_xml_path)
            self.assertIsInstance(result, etree.XMLSyntaxError)
        finally:
            os.unlink(tmp_xml_path)

    def test_validar_schema_returns_iter_errors_when_schema_is_invalid(self):
        schema = MagicMock()
        schema.is_valid.return_value = False
        schema.iter_errors.return_value = ["erro-schema"]

        with patch("config.functions.etree.parse"), \
                patch("config.functions.xmlschema.XMLSchema", return_value=schema):
            result = functions.validar_schema("schema.xsd", "arquivo.xml")

        self.assertEqual(result, ["erro-schema"])
        schema.is_valid.assert_called_once_with("arquivo.xml")
        schema.iter_errors.assert_called_once_with("arquivo.xml")

    def test_validar_schema_returns_none_when_schema_is_valid(self):
        schema = MagicMock()
        schema.is_valid.return_value = True

        with patch("config.functions.etree.parse"), \
                patch("config.functions.xmlschema.XMLSchema", return_value=schema):
            result = functions.validar_schema("schema.xsd", "arquivo.xml")

        self.assertIsNone(result)
