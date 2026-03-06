import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import RequestFactory, SimpleTestCase

from apps.esocial.views.parsing_post import (
    parsing_post,
    parsing_post_to_json,
    set_nested_value,
    transform_to_list,
)


class ParsingPostHelpersTests(SimpleTestCase):

    def test_set_nested_value_cria_estrutura_aninhada(self):
        data = {}
        set_nested_value(data, ["pai", "filho", "valor"], "10")
        self.assertEqual(data, {"pai": {"filho": {"valor": "10"}}})

    def test_transform_to_list_converte_indices_numericos_e_recursivo(self):
        payload = {
            "itens": {
                "1": {"nome": "B"},
                "0": {"nome": "A"},
            },
            "meta": {"tipo": "x"},
            "valor": "1",
        }

        transformed = transform_to_list(payload)
        self.assertEqual(transformed["itens"], [{"nome": "A"}, {"nome": "B"}])
        self.assertEqual(transformed["meta"], {"tipo": "x"})
        self.assertEqual(transformed["valor"], "1")

    def test_parsing_post_to_json_processa_campos_com_colchetes(self):
        form_data = {
            "evento[itens][0][codigo]": "001",
            "evento[itens][0][descricao]": "Primeiro",
            "evento[itens][1][codigo]": "002",
            "ignorar": "x",
        }

        parsed = parsing_post_to_json(form_data)
        self.assertEqual(parsed["eventoitens"][0]["codigo"], "001")
        self.assertEqual(parsed["eventoitens"][1]["codigo"], "002")
        self.assertNotIn("ignorar", parsed)


class ParsingPostViewTests(SimpleTestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = SimpleNamespace(is_authenticated=True)

    def test_parsing_post_salva_evento_quando_metodo_post(self):
        data = {"evento[campo]": "valor"}
        request = self.factory.post(
            "/esocial/parsing-post/1",
            data=json.dumps(data),
            content_type="application/json",
        )
        request.user = self.user

        evento = SimpleNamespace(evento_json="", save=MagicMock())

        with patch("apps.esocial.views.parsing_post.get_object_or_404", return_value=evento):
            response = parsing_post(request, 1)

        payload = json.loads(response.content.decode())
        self.assertEqual(payload, {"eventocampo": "valor"})
        self.assertEqual(json.loads(evento.evento_json), {"eventocampo": "valor"})
        evento.save.assert_called_once()

    def test_parsing_post_retorna_json_vazio_para_metodo_nao_post(self):
        request = self.factory.get("/esocial/parsing-post/1")
        request.user = self.user

        evento = SimpleNamespace(evento_json="", save=MagicMock())
        with patch("apps.esocial.views.parsing_post.get_object_or_404", return_value=evento):
            response = parsing_post(request, 1)

        self.assertEqual(json.loads(response.content.decode()), {})
        evento.save.assert_not_called()
