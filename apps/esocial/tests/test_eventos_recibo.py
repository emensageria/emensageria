import tempfile
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import RequestFactory, SimpleTestCase

from apps.esocial.views.eventos_recibo import eventos_recibo, get_size_image, pdf_recibo_evento


class _EventoFake:

    def __init__(self, arquivo_pdf, retorno_envio, retorno_consulta, lote):
        self.identidade = "ID123"
        self.versao = "1.0"
        self.verproc = "PROC"
        self.nrinsc = "123456789"
        self.retorno_envio_lote_json = retorno_envio
        self.retorno_consulta_json = retorno_consulta
        self.lote = lote
        self._arquivo_pdf = arquivo_pdf

    def pdf_file(self):
        return self._arquivo_pdf

    @staticmethod
    def get_evento_display():
        return "Evento X"

    @staticmethod
    def get_tpamb_display():
        return "Produção"

    @staticmethod
    def get_procemi_display():
        return "Aplicativo"

    @staticmethod
    def get_tpinsc_display():
        return "CNPJ"


class EventosReciboTests(SimpleTestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = SimpleNamespace(is_authenticated=True)

    def test_get_size_image_retorna_dimensoes(self):
        image = MagicMock()
        image.getSize.return_value = (100, 50)

        with patch("apps.esocial.views.eventos_recibo.utils.ImageReader", return_value=image):
            width, height = get_size_image("/tmp/logo.png")

        self.assertEqual((width, height), (100, 50))

    def test_pdf_recibo_evento_fluxo_recepcao_sem_consulta(self):
        transmissor = SimpleNamespace(
            logotipo=SimpleNamespace(file=SimpleNamespace(name="logo.png")),
            endereco_completo="Rua A\nBairro B",
        )
        lote = SimpleNamespace(transmissor=transmissor)

        retorno_envio = {
            "dadosRecepcaoLote": {
                "tpAmb": "2",
                "dhRecepcao": "2024-01-01",
                "versaoAplicativoRecepcao": "v1",
                "protocoloEnvio": "P1",
            },
            "status": {"cdResposta": "201", "descResposta": "OK"},
        }
        retorno_consulta = {}
        canvas_mock = MagicMock()
        evento = _EventoFake("/tmp/recibo_a.pdf", retorno_envio, retorno_consulta, lote)

        with patch("apps.esocial.views.eventos_recibo.canvas.Canvas", return_value=canvas_mock), \
                patch("config.functions.create_dir"), \
                patch("apps.esocial.views.eventos_recibo.get_size_image", return_value=(120, 60)):
            pdf_recibo_evento(evento)

        canvas_mock.setTitle.assert_called_once()
        canvas_mock.drawImage.assert_called()
        canvas_mock.save.assert_called_once()

    def test_pdf_recibo_evento_fluxo_processamento_com_ocorrencia_dict(self):
        retorno_envio = {}
        retorno_consulta = {
            "recepcao": {"tpAmb": "1"},
            "processamento": {
                "cdResposta": "200",
                "descResposta": "Processado",
                "versaoAppProcessamento": "v2",
                "dhProcessamento": "2024-01-02",
                "ocorrencias": {
                    "ocorrencia": {
                        "tipo": "A",
                        "codigo": "10",
                        "descricao": " ".join(["descricao"] * 40),
                        "localizacao": "/eSocial/evt",
                    }
                },
            },
            "recibo": {"nrRecibo": "R123", "hash": "HASH"},
        }
        canvas_mock = MagicMock()
        evento = _EventoFake("/tmp/recibo_b.pdf", retorno_envio, retorno_consulta, lote=None)

        with patch("apps.esocial.views.eventos_recibo.canvas.Canvas", return_value=canvas_mock), \
                patch("config.functions.create_dir"):
            pdf_recibo_evento(evento)

        canvas_mock.drawString.assert_called()
        canvas_mock.save.assert_called_once()

    def test_pdf_recibo_evento_cobre_branches_parciais_de_recepcao_e_processamento(self):
        class CoCustom:
            def __init__(self):
                self.proc_calls = 0

            def get(self, key):
                if key == "recepcao":
                    return {}
                if key == "processamento":
                    self.proc_calls += 1
                    if self.proc_calls == 1:
                        return {"placeholder": True}
                    return {}
                if key == "recibo":
                    return None
                return None

        retorno_envio = {"status": {"cdResposta": "100", "descResposta": "OK"}}
        retorno_consulta = CoCustom()
        canvas_mock = MagicMock()
        evento = _EventoFake("/tmp/recibo_branch.pdf", retorno_envio, retorno_consulta, lote=None)

        with patch("apps.esocial.views.eventos_recibo.canvas.Canvas", return_value=canvas_mock), \
                patch("config.functions.create_dir"):
            pdf_recibo_evento(evento)

        canvas_mock.drawString.assert_called()
        canvas_mock.save.assert_called_once()

    def test_pdf_recibo_evento_fluxo_processamento_lista_e_sem_localizacao(self):
        retorno_envio = {}
        retorno_consulta = {
            "processamento": {
                "cdResposta": "200",
                "descResposta": "OK",
                "versaoAppProcessamento": "v2",
                "dhProcessamento": "2024-01-02",
                "ocorrencias": {
                    "ocorrencia": [
                        {
                            "tipo": "A",
                            "codigo": "10",
                            "descricao": "Descricao A",
                            "localizacao": "",
                        },
                        {
                            "tipo": "B",
                            "codigo": "11",
                            "descricao": "Descricao B",
                        },
                    ]
                },
            }
        }
        canvas_mock = MagicMock()
        evento = _EventoFake("/tmp/recibo_c.pdf", retorno_envio, retorno_consulta, lote=None)

        with patch("apps.esocial.views.eventos_recibo.canvas.Canvas", return_value=canvas_mock), \
                patch("config.functions.create_dir"):
            pdf_recibo_evento(evento)

        canvas_mock.drawString.assert_called()
        canvas_mock.save.assert_called_once()

    def test_pdf_recibo_evento_fluxo_processamento_sem_ocorrencias(self):
        retorno_envio = {}
        retorno_consulta = {
            "processamento": {
                "cdResposta": "200",
                "descResposta": "OK",
                "versaoAppProcessamento": "v2",
                "dhProcessamento": "2024-01-02",
            }
        }
        canvas_mock = MagicMock()
        evento = _EventoFake("/tmp/recibo_d.pdf", retorno_envio, retorno_consulta, lote=None)

        with patch("apps.esocial.views.eventos_recibo.canvas.Canvas", return_value=canvas_mock), \
                patch("config.functions.create_dir"):
            pdf_recibo_evento(evento)

        canvas_mock.drawString.assert_called()
        canvas_mock.save.assert_called_once()

    def test_pdf_recibo_evento_cobre_branch_recepcao_com_segunda_leitura_falsa(self):
        class CoRecepcaoCustom:
            def __init__(self):
                self.recepcao_calls = 0

            def get(self, key):
                if key == "recepcao":
                    self.recepcao_calls += 1
                    if self.recepcao_calls == 1:
                        return {"tpAmb": "1"}
                    return {}
                if key == "processamento":
                    return None
                return None

        canvas_mock = MagicMock()
        evento = _EventoFake("/tmp/recibo_recepcao.pdf", {}, CoRecepcaoCustom(), lote=None)

        with patch("apps.esocial.views.eventos_recibo.canvas.Canvas", return_value=canvas_mock), \
                patch("config.functions.create_dir"):
            pdf_recibo_evento(evento)

        canvas_mock.drawString.assert_called()
        canvas_mock.save.assert_called_once()

    def test_eventos_recibo_retorna_pdf_inline(self):
        request = self.factory.get("/esocial/eventos-recibo/1")
        request.user = self.user

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(b"%PDF-test")
            tmp_path = tmp.name

        evento = _EventoFake(tmp_path, {}, {}, lote=None)

        with patch("apps.esocial.views.eventos_recibo.get_object_or_404", return_value=evento), \
                patch("apps.esocial.views.eventos_recibo.pdf_recibo_evento") as pdf_mock:
            response = eventos_recibo(request, 1)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("inline; filename=ID123.pdf", response["Content-Disposition"])
        pdf_mock.assert_called_once_with(evento)
