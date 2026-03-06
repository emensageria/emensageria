from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from rest_framework.serializers import ValidationError

from apps.esocial.api.serializers import EventosSerializer, remove_ns_prefixes
from apps.esocial.choices import EVENTO_ORIGEM_API, STATUS_EVENTO_IMPORTADO
from config.settings import ESOCIAL_TPAMB


class RemoveNsPrefixesTests(SimpleTestCase):

    def test_remove_ns_prefixes_remove_prefixos_em_dict_lista_e_valor(self):
        payload = {
            "ns0:eSocial": {
                "ns1:evento": [
                    {"ns2:campo": "valor"},
                    "texto",
                ]
            }
        }

        cleaned = remove_ns_prefixes(payload)

        self.assertEqual(
            cleaned,
            {"eSocial": {"evento": [{"campo": "valor"}, "texto"]}},
        )
        self.assertEqual(remove_ns_prefixes("abc"), "abc")


class EventosSerializerTests(SimpleTestCase):

    def setUp(self):
        self.serializer = EventosSerializer()

    def test_create_com_evento_xml_gera_evento_json_e_xml(self):
        validated_data = {
            "versao": "v_S_01_03_00",
            "evento": "s1000",
            "evento_xml": (
                '<ns0:eSocial xmlns:ns0="urn:x"><ns0:evt><ns0:a>1</ns0:a>'
                "</ns0:evt></ns0:eSocial>"
            ),
            "evento_json": None,
        }
        fake_instance = SimpleNamespace(create_xml=Mock())
        with patch(
            "rest_framework.serializers.ModelSerializer.create",
            return_value=fake_instance,
        ) as mocked_create:
            result = self.serializer.create(validated_data)

        self.assertIs(result, fake_instance)
        mocked_create.assert_called_once()
        fake_instance.create_xml.assert_called_once_with()
        self.assertEqual(validated_data["origem"], EVENTO_ORIGEM_API)
        self.assertEqual(validated_data["is_aberto"], False)
        self.assertEqual(validated_data["status"], STATUS_EVENTO_IMPORTADO)
        self.assertEqual(validated_data["tpamb"], ESOCIAL_TPAMB)
        self.assertEqual(validated_data["evento_json"]["evt"], {"a": "1"})

    def test_create_sem_parse_quando_evento_json_ja_existe(self):
        validated_data = {
            "versao": "v_S_01_03_00",
            "evento": "s1000",
            "evento_xml": "<xml/>",
            "evento_json": {"ja": "pronto"},
        }
        fake_instance = SimpleNamespace(create_xml=Mock())

        with patch("apps.esocial.api.serializers.xmltodict.parse") as mocked_parse, patch(
            "rest_framework.serializers.ModelSerializer.create",
            return_value=fake_instance,
        ):
            self.serializer.create(validated_data)

        mocked_parse.assert_not_called()
        fake_instance.create_xml.assert_called_once_with()

    def test_update_com_evento_xml_limpa_campos_retorno_e_gera_xml(self):
        validated_data = {
            "evento_xml": '<ns0:eSocial xmlns:ns0="urn:x"><ns0:evt/></ns0:eSocial>',
            "evento_json": None,
        }
        fake_instance = SimpleNamespace(create_xml=Mock())
        current = SimpleNamespace()

        with patch(
            "rest_framework.serializers.ModelSerializer.update",
            return_value=fake_instance,
        ) as mocked_update:
            result = self.serializer.update(current, validated_data)

        self.assertIs(result, fake_instance)
        mocked_update.assert_called_once_with(current, validated_data)
        self.assertEqual(validated_data["origem"], EVENTO_ORIGEM_API)
        self.assertEqual(validated_data["is_aberto"], False)
        self.assertEqual(validated_data["status"], STATUS_EVENTO_IMPORTADO)
        self.assertEqual(validated_data["tpamb"], ESOCIAL_TPAMB)
        self.assertEqual(validated_data["ocorrencias_json"], None)
        self.assertEqual(validated_data["retorno_envio_json"], {})
        self.assertEqual(validated_data["retorno_consulta_json"], {})
        self.assertEqual(validated_data["evento_json"]["evt"], None)
        fake_instance.create_xml.assert_called_once_with()

    def test_update_sem_parse_quando_evento_json_ja_existe(self):
        validated_data = {
            "evento_xml": "<xml/>",
            "evento_json": {"ja": "pronto"},
        }

        with patch("apps.esocial.api.serializers.xmltodict.parse") as mocked_parse, patch(
            "rest_framework.serializers.ModelSerializer.update",
            return_value=SimpleNamespace(create_xml=Mock()),
        ):
            self.serializer.update(SimpleNamespace(), validated_data)

        mocked_parse.assert_not_called()

    def test_validate_retorna_dados_quando_evento_compativel(self):
        data = {"versao": "v_S_01_03_00", "evento": "s1000"}

        self.assertEqual(self.serializer.validate(data), data)

    def test_validate_lanca_erro_quando_evento_invalido(self):
        data = {"versao": "v_S_01_03_00", "evento": "nao-existe"}

        with self.assertRaises(ValidationError):
            self.serializer.validate(data)
