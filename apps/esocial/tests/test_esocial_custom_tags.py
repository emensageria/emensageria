import importlib
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

import apps.esocial.templatetags.esocial_custom_tags as tags


class _NoDictObject:
    __slots__ = ()


class _WidgetField:

    def as_widget(self, attrs):
        return attrs


class EsocialCustomTagsTests(SimpleTestCase):

    def test_module_reload_cobre_sucesso_e_erros_de_locale(self):
        with patch("locale.setlocale", return_value="pt_BR.UTF-8"):
            importlib.reload(tags)

        logger_mock = MagicMock()
        with patch("logging.getLogger", return_value=logger_mock), patch(
            "locale.setlocale",
            side_effect=[Exception("erro 1"), Exception("erro 2")],
        ):
            importlib.reload(tags)

        logger_mock.error.assert_called()
        logger_mock.critical.assert_called()

    def test_is_list(self):
        self.assertTrue(tags.is_list([1, 2]))
        self.assertFalse(tags.is_list((1, 2)))

    def test_finditem_dict_e_lista(self):
        self.assertEqual(tags.finditem({"a": 1}, "a"), 1)
        self.assertEqual(tags.finditem({"a": {"b": 2}}, "b"), 2)
        self.assertIsNone(tags.finditem([{"a": 1}], "a"))
        self.assertIsNone(tags.finditem({}, "z"))
        self.assertIsNone(tags.finditem({"a": 1, "b": 2}, "z"))
        self.assertIsNone(tags.finditem({"a": {"x": 1}, "b": {"y": 2}}, "z"))
        self.assertIsNone(tags.finditem([], "z"))
        self.assertIsNone(tags.finditem("texto", "z"))

    def test_read_ocorrencias_cobre_todos_os_formatos(self):
        payload_list = json.dumps(
            [{"ocorrencia": {"tipo": 1, "codigo": 2, "descricao": "d", "localizacao": "l"}}]
        )
        payload_dict_ocorrencias_list = json.dumps(
            {
                "ocorrencias": {
                    "ocorrencia": [{"tipo": 1, "codigo": 2, "descricao": "d", "localizacao": "l"}]
                }
            }
        )
        payload_dict_ocorrencia_dict = json.dumps(
            {"ocorrencia": {"tipo": 1, "codigo": 2, "descricao": "d", "localizacao": "l"}}
        )
        payload_dict_ocorrencia_list = json.dumps(
            {"ocorrencia": [{"tipo": 1, "codigo": 2, "descricao": "d", "localizacao": "l"}]}
        )
        payload_dict_ocorrencias_plain_list = json.dumps(
            {
                "ocorrencias": [
                    {"ocorrencia": {"tipo": 1, "codigo": 2, "descricao": "d", "localizacao": "l"}}
                ]
            }
        )

        self.assertEqual(tags.read_ocorrencias(payload_list)[0]["tipo"], 1)
        self.assertEqual(tags.read_ocorrencias(payload_dict_ocorrencias_list)[0]["codigo"], 2)
        self.assertEqual(tags.read_ocorrencias(payload_dict_ocorrencia_dict)[0]["descricao"], "d")
        self.assertEqual(tags.read_ocorrencias(payload_dict_ocorrencia_list)[0]["localizacao"], "l")
        self.assertEqual(tags.read_ocorrencias(payload_dict_ocorrencias_plain_list)[0]["tipo"], 1)

        with self.assertRaises(Exception):
            tags.read_ocorrencias(json.dumps({"foo": "bar"}))

    def test_read_ocorrencias_lote(self):
        self.assertEqual(
            tags.read_ocorrencias_lote(
                {"ocorrencia": [{"tipo": 1, "codigo": 2, "descricao": "d", "localizacao": "l"}]}
            )[0]["tipo"],
            1,
        )
        self.assertEqual(
            tags.read_ocorrencias_lote(
                {"ocorrencia": {"tipo": 1, "codigo": 2, "descricao": "d", "localizacao": "l"}}
            )[0]["codigo"],
            2,
        )

    def test_get_tipo_erro(self):
        self.assertEqual(tags.get_tipo_erro("1"), "ERRO")
        self.assertEqual(tags.get_tipo_erro("2"), "ADVERTÊNCIA")

    def test_to_json(self):
        self.assertEqual(tags.to_json('{"a": 1}')["a"], 1)
        with patch.object(tags.logger, "error"):
            self.assertEqual(tags.to_json("invalido"), "")
        with patch(
            "apps.esocial.templatetags.esocial_custom_tags.json.loads",
            side_effect=Exception("x"),
        ), patch.object(tags.logger, "error"):
            self.assertEqual(tags.to_json('{"a": 1}'), "")

    def test_is_form_exists_e_get_event_form(self):
        obj = SimpleNamespace(versao="v1", evento="s1000")
        with patch("pathlib.Path.is_file", return_value=True):
            self.assertTrue(tags.is_form_exists(obj))
        with patch("pathlib.Path.is_file", return_value=False):
            self.assertFalse(tags.is_form_exists(obj))
        self.assertEqual(tags.get_event_form(obj), "v1/s1000.html")

    def test_disabled(self):
        self.assertEqual(tags.disabled(SimpleNamespace(is_aberto=False)), 'disabled="disabled"')
        self.assertEqual(tags.disabled(SimpleNamespace(is_aberto=True)), "")

    def test_test_filter(self):
        self.assertEqual(tags.test(SimpleNamespace(a=1)), "")
        self.assertEqual(tags.test(_NoDictObject()), "")

    def test_readjson(self):
        self.assertEqual(tags.readjson("", "a"), "")
        self.assertEqual(tags.readjson({"a": {"b": 3}}, "a.b"), 3)
        self.assertEqual(tags.readjson('{"a": 1}', "inexistente"), "")

    def test_render_with_model_dict(self):
        obj = SimpleNamespace(nome="Ana")
        self.assertEqual(tags.render_with_model_dict("%(nome)s", obj), "Ana")
        self.assertEqual(tags.render_with_model_dict("", obj), "")

    def test_filters_de_transformacao_simples(self):
        self.assertEqual(tags.to_sql("O'Hara"), "O''Hara")
        self.assertEqual(tags.to_list("a,b"), ["a", "b"])
        self.assertEqual(tags.data_en_to_br("2024-03-01"), "01/03/2024")
        self.assertTrue(tags.is_int("12"))
        with patch.object(tags.logger, "error"):
            self.assertFalse(tags.is_int("xx"))
        self.assertEqual(tags.multiply(2, 3), 6)
        self.assertEqual(tags.underline_to_hyphen("a_b"), "a-b")
        self.assertEqual(tags.format_number_2dec_xml_reinf(1.2), "1,2")
        self.assertEqual(tags.format_number_4dec_xml_reinf(1.2345), "1,2345")
        self.assertEqual(tags.replace_aspas("a'b"), 'a"b')
        self.assertEqual(tags.replace_aspas(None), "")
        self.assertEqual(tags.format_number_2dec_xml(1.2), "1.20")
        self.assertEqual(tags.format_number_4dec_xml(1.2), "1.2000")
        self.assertEqual(tags.inteiro_xml("10"), "10")
        self.assertEqual(tags.dec_to_int("10"), 10)
        self.assertEqual(tags.valor("1.234"), "1234")
        self.assertEqual(tags.to_str(99), "99")
        self.assertEqual(tags.base64_encode_me(b"ab"), b"YWI=")
        self.assertEqual(tags.notNone("x"), "x")
        self.assertEqual(tags.notNone(""), "")
        self.assertEqual(tags.inteiro("10.99"), 10)
        self.assertEqual(tags.padrao_americano("1,23"), "1,23")

    def test_query_filter(self):
        qs = MagicMock()
        qs.filter.return_value = "filtrado"
        self.assertEqual(tags.query(qs, status=1), "filtrado")
        qs.filter.assert_called_once_with(status=1)

    def test_to_xml(self):
        self.assertEqual(tags.to_xml("<a>'\"&"), "&amp;lt;a&amp;gt;&apos;&quot;&amp;")
        self.assertEqual(tags.to_xml(None), "")

    def test_filters_json_string(self):
        self.assertEqual(tags.json_tab("{}", "aba"), '{"tab": "aba"}')
        self.assertEqual(tags.json_tab('{"x":1}', "aba"), '{"x":1, "tab": "aba"}')
        self.assertEqual(tags.json_return_page("{}", "1"), '{"return_page": "1"}')
        self.assertEqual(tags.json_return_page('{"x":1}', "1"), '{"x":1, "return_page": "1"}')
        self.assertEqual(tags.json_return_hash("{}", "h"), '{"return_hash": "h"}')
        self.assertEqual(tags.json_return_hash('{"x":1}', "h"), '{"x":1, "return_hash": "h"}')
        self.assertEqual(tags.json_id("{}", "9"), '{"id": "9"}')
        self.assertEqual(tags.json_id('{"x":1}', "9"), '{"x":1, "id": "9"}')
        self.assertEqual(tags.json_print("{}", "s"), '{"print": "s"}')
        self.assertEqual(tags.json_print('{"x":1}', "s"), '{"x":1, "print": "s"}')

    def test_dv_maker_e_validate_cpf(self):
        self.assertEqual(tags.DV_maker(5), 6)
        self.assertEqual(tags.DV_maker(1), 0)
        self.assertFalse(tags.validate_CPF(""))
        self.assertFalse(tags.validate_CPF("abc"))
        self.assertFalse(tags.validate_CPF("1234567890"))
        self.assertFalse(tags.validate_CPF("52998224724"))
        self.assertTrue(tags.validate_CPF("529.982.247-25"))

    def test_add_filters_e_get_permissao(self):
        self.assertEqual(tags.addstr("a", 1), "a1")
        self.assertEqual(tags.add("a", 1), "a|1")
        self.assertFalse(tags.get_permissao({"1": 0}, 1))
        self.assertTrue(tags.get_permissao({"1": 1}, 1))
        self.assertFalse(tags.get_permissao({"1": 2}, 1))
        with patch.object(tags.logger, "error"):
            self.assertFalse(tags.get_permissao({}, 1))

    def test_divide(self):
        self.assertEqual(tags.divide(None, None), 100)
        self.assertEqual(tags.divide(20, 40), 50)

    def test_get_value_from_dict(self):
        self.assertEqual(tags.get_value_from_dict({"k": "2"}, "k"), 2)
        self.assertEqual(tags.get_value_from_dict({"k": "0"}, "k"), "")
        with patch.object(tags.logger, "error"):
            self.assertEqual(tags.get_value_from_dict({"k": "abc"}, "k"), "abc")
        with patch.object(tags.logger, "error"):
            self.assertEqual(tags.get_value_from_dict({}, "k"), "")
        with patch.object(tags.logger, "error"):
            self.assertEqual(tags.get_value_from_dict({"k": 1}, None), "")

    def test_addcss(self):
        field = _WidgetField()
        self.assertEqual(tags.addcss(field, "x"), {"class": "x"})
        self.assertEqual(tags.addcss_select2(field, "x"), {"class": "x", "style": "width: 100%"})

    def test_mes_ano_cobre_todos_os_meses(self):
        meses = {
            "01": "Jan/",
            "02": "Fev/",
            "03": "Mar/",
            "04": "Abr/",
            "05": "Mai/",
            "06": "Jun/",
            "07": "Jul/",
            "08": "Ago/",
            "09": "Set/",
            "10": "Out/",
            "11": "Nov/",
            "12": "Dez/",
        }
        for mes, nome in meses.items():
            self.assertEqual(tags.mes_ano(f"2024{mes}"), f"{nome}24")

    def test_ano_mes_extenso_cobre_todos_os_meses(self):
        meses = {
            "01": "Janeiro",
            "02": "Fevereiro",
            "03": "Março",
            "04": "Abril",
            "05": "Maio",
            "06": "Junho",
            "07": "Julho",
            "08": "Agosto",
            "09": "Setembro",
            "10": "Outubro",
            "11": "Novembro",
            "12": "Dezembro",
        }
        for mes, nome in meses.items():
            self.assertEqual(tags.ano_mes_extenso(f"2024-{mes}"), f"{nome}/2024")
        with self.assertRaises(UnboundLocalError):
            tags.ano_mes_extenso("2024-13")

    def test_total_quant_e_percentage(self):
        self.assertEqual(tags.total_quant([{"v": 2}, {"v": 3}], "v"), 5)
        self.assertEqual(tags.percentage(1, 4), "25.00%")
        self.assertEqual(tags.percentage("x", 4), "")
