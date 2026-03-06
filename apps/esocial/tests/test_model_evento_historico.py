from django.test import SimpleTestCase

from apps.esocial.models.evento_historico import EventosHistorico


class EventosHistoricoModelTests(SimpleTestCase):

    def test_str_retorna_identidade(self):
        historico = EventosHistorico(identidade="ID-HIST-001")
        self.assertEqual(str(historico), "ID-HIST-001")
