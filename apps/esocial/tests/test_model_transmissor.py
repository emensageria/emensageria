from unittest.mock import patch

from django.test import SimpleTestCase

from apps.esocial.models.certificado import Certificados
from apps.esocial.models.transmissor import Transmissor


class TransmissorModelTests(SimpleTestCase):

    def test_str_retorna_nome_empresa(self):
        transmissor = Transmissor(nome_empresa="Empresa XPTO")
        self.assertEqual(str(transmissor), "Empresa XPTO")

    def test_save_remove_caracteres_nao_numericos_dos_campos_inscricao(self):
        transmissor = Transmissor(
            transmissor_nrinsc="12.345.678/0001-99",
            nrinsc="98.765.432/0001-11",
            nome_empresa="Empresa XPTO",
            transmissor_tpinsc=1,
            tpinsc=1,
            certificado=Certificados(),
        )

        with patch("django.db.models.base.Model.save", return_value=None) as save_mock:
            transmissor.save()

        self.assertEqual(transmissor.transmissor_nrinsc, "12345678000199")
        self.assertEqual(transmissor.nrinsc, "98765432000111")
        save_mock.assert_called_once()
