import json
from types import SimpleNamespace
from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase

from apps.esocial.views.dashboard_json import dashboard_json


class _FakeQuerySet:

    def __init__(self, count_value, values_data):
        self._count_value = count_value
        self._values_data = values_data

    def count(self):
        return self._count_value

    def values(self, *_args):
        return self._values_data


class DashboardJsonViewTests(SimpleTestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = SimpleNamespace(is_authenticated=True)

    def test_dashboard_json_retorna_contadores_e_listas(self):
        request = self.factory.get("/esocial/dashboard-json")
        request.user = self.user

        filtros = [
            _FakeQuerySet(1, [{"id": 1, "evento": "A", "identidade": "I1"}]),
            _FakeQuerySet(2, [{"id": 2, "evento": "B", "identidade": "I2"}]),
            _FakeQuerySet(3, [{"id": 3, "evento": "C", "identidade": "I3"}]),
            _FakeQuerySet(4, [{"id": 4, "evento": "D", "identidade": "I4"}]),
            _FakeQuerySet(5, [{"id": 5, "evento": "E", "identidade": "I5"}]),
            _FakeQuerySet(6, [{"id": 6, "evento": "F", "identidade": "I6"}]),
        ]

        with patch("apps.esocial.views.dashboard_json.Eventos.objects.filter", side_effect=filtros):
            response = dashboard_json(request)

        payload = json.loads(response.content.decode())
        self.assertEqual(payload["esocial_quant_importados"], 1)
        self.assertEqual(payload["esocial_quant_cadastrados"], 2)
        self.assertEqual(payload["esocial_quant_erros"], 3)
        self.assertEqual(payload["esocial_quant_validados"], 4)
        self.assertEqual(payload["esocial_quant_enviados"], 5)
        self.assertEqual(payload["esocial_quant_processados"], 6)
        self.assertEqual(payload["esocial_importados"][0]["id"], 1)
        self.assertEqual(payload["esocial_processados"][0]["id"], 6)
