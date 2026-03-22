from typing import Dict, List

from config.settings import CURL_PATH

TPAMB = {
    'Produção': 1,
    'Produção Restrita': 2,
}

CHOICES_PRODUCTION = [
    '1', 'prod'
]

URLS_ESOCIAL = {
    'Produção': {
        'WsEnviarLoteEventos': {
            'url': 'https://webservices.envio.esocial.gov.br/servicos/empregador/'
                   'enviarloteeventos/WsEnviarLoteEventos.svc',
            'action': 'http://www.esocial.gov.br/servicos/empregador/lote/eventos/envio/v1_1_0/'
                      'ServicoEnviarLoteEventos/EnviarLoteEventos',
        },
        'WsConsultarLoteEventos': {
            'url': 'https://webservices.consulta.esocial.gov.br/servicos/empregador/'
                   'consultarloteeventos/WsConsultarLoteEventos.svc',
            'action': 'http://www.esocial.gov.br/servicos/empregador/lote/eventos/envio/'
                      'consulta/retornoProcessamento/v1_1_0/ServicoConsultarLoteEventos/'
                      'ConsultarLoteEventos',
        },
    },
    'Produção Restrita': {
        'WsEnviarLoteEventos': {
            'url': 'https://webservices.producaorestrita.esocial.gov.br/servicos'
                   '/empregador/enviarloteeventos/WsEnviarLoteEventos.svc?wsdl',
            'action': 'http://www.esocial.gov.br/servicos/empregador/lote/eventos/envio/v1_1_0/'
                      'ServicoEnviarLoteEventos/EnviarLoteEventos',
        },
        'WsConsultarLoteEventos': {
            'url': 'https://webservices.producaorestrita.esocial.gov.br/servicos/empregador/'
                   'consultarloteeventos/WsConsultarLoteEventos.svc',
            'action': 'http://www.esocial.gov.br/servicos/empregador/lote/eventos/envio/'
                      'consulta/retornoProcessamento/v1_1_0/ServicoConsultarLoteEventos/'
                      'ConsultarLoteEventos',
        },
    },
}

COMMAND_CURL = CURL_PATH + 'curl --insecure --connect-timeout %(timeout)s ' \
    '--cert %(cert)s --key %(key)s --capath %(capath)s ' \
    '-H "Content-Type: text/xml;charset=UTF-8" ' \
    '-H "SOAPAction:%(action)s" ' \
    '--dump-header %(header)s ' \
    '--output %(response)s ' \
    '-d@%(request)s %(url)s'

MAKE_SEND = """
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:v1="http://www.esocial.gov.br/servicos/empregador/lote/eventos/envio/v1_1_0">
    <soapenv:Header/>
    <soapenv:Body>
        <v1:EnviarLoteEventos>
            <v1:loteEventos>
                <eSocial xmlns="http://www.esocial.gov.br/schema/lote/eventos/envio/v1_1_1">
                    <envioLoteEventos grupo="{}">
                        <ideEmpregador>
                            <tpInsc>{}</tpInsc>
                            <nrInsc>{}</nrInsc>
                        </ideEmpregador>
                        <ideTransmissor>
                            <tpInsc>{}</tpInsc>
                            <nrInsc>{}</nrInsc>
                        </ideTransmissor>
                        <eventos>{}</eventos>
                    </envioLoteEventos>
                </eSocial>
            </v1:loteEventos>
        </v1:EnviarLoteEventos>
    </soapenv:Body>
</soapenv:Envelope>"""

MAKE_RETRIEVE = """
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:v1="http://www.esocial.gov.br/servicos/empregador/lote/eventos/envio/consulta/retornoProcessamento/v1_1_0">
    <soapenv:Header/>
    <soapenv:Body>
        <v1:ConsultarLoteEventos>
            <v1:consulta>
                <eSocial xmlns="http://www.esocial.gov.br/schema/lote/eventos/envio/consulta/retornoProcessamento/v1_0_0"
                         xmlns:xs="http://www.w3.org/2001/XMLSchema">
                    <consultaLoteEventos>
                        <protocoloEnvio>{}</protocoloEnvio>
                    </consultaLoteEventos>
                </eSocial>
            </v1:consulta>
        </v1:ConsultarLoteEventos>
    </soapenv:Body>
</soapenv:Envelope>"""  # noqa: E501

STATUS_EVENTO_IMPORTADO = -1
STATUS_EVENTO_CADASTRADO = 0
STATUS_EVENTO_ERRO = 1
STATUS_EVENTO_AGUARD_ENVIO = 2
STATUS_EVENTO_ENVIADO = 3
STATUS_EVENTO_PROCESSADO = 5
STATUS_EVENTO_ENVIANDO = 6
STATUS_EVENTO_CONSULTANDO = 7

EVENTO_STATUS = [
    (STATUS_EVENTO_IMPORTADO, 'Importado pela API'),
    (STATUS_EVENTO_CADASTRADO, 'Cadastrado (Aguardando validação)'),
    (STATUS_EVENTO_ERRO, 'Erro (Aguardando correção)'),
    # (STATUS_EVENTO_ERRO, 'Erro (Aguardando correção)'),
    (STATUS_EVENTO_AGUARD_ENVIO, 'Validado (Aguardando envio)'),
    (STATUS_EVENTO_ENVIANDO, 'Enviando ...'),
    (STATUS_EVENTO_ENVIADO, 'Enviado (Aguardando consulta)'),
    (STATUS_EVENTO_CONSULTANDO, 'Consultando ...'),
    (STATUS_EVENTO_PROCESSADO, 'Consultado'),
]

STATUS_TRANSMISSOR_CADASTRADO = 0
STATUS_TRANSMISSOR_ASSINADO = 8
STATUS_TRANSMISSOR_AGUARDANDO = 1
STATUS_TRANSMISSOR_ENVIANDO = 2
STATUS_TRANSMISSOR_ENVIADO = 3
STATUS_TRANSMISSOR_ERRO_ENVIO = 4
STATUS_TRANSMISSOR_CONSULTANDO = 5
STATUS_TRANSMISSOR_CONSULTADO = 6
STATUS_TRANSMISSOR_ERRO_CONSULTA = 7

TRANSMISSOR_STATUS = [
    (STATUS_TRANSMISSOR_CADASTRADO, 'Cadastrado'),
    (STATUS_TRANSMISSOR_ASSINADO, 'Assinado'),
    (STATUS_TRANSMISSOR_AGUARDANDO, 'Aguardando envio'),
    (STATUS_TRANSMISSOR_ENVIANDO, 'Enviando ...'),
    (STATUS_TRANSMISSOR_ENVIADO, 'Enviado'),
    (STATUS_TRANSMISSOR_ERRO_ENVIO, 'Erro no envio'),
    (STATUS_TRANSMISSOR_CONSULTANDO, 'Consultando ...'),
    (STATUS_TRANSMISSOR_CONSULTADO, 'Consultado'),
    (STATUS_TRANSMISSOR_ERRO_CONSULTA, 'Erro na consulta'),
]

EVENTOS_GRUPOS_TABELAS = 1
EVENTOS_GRUPOS_NAO_PERIODICOS = 2
EVENTOS_GRUPOS_PERIODICOS = 3

EVENTOS_GRUPOS = [
    (EVENTOS_GRUPOS_TABELAS, '1 - Eventos de Tabelas'),
    (EVENTOS_GRUPOS_NAO_PERIODICOS, '2 - Eventos Não Periódicos'),
    (EVENTOS_GRUPOS_PERIODICOS, '3 - Eventos Periódicos'),
]

ESOCIAL_VERSAO_DEFAULT = 'v_S_01_03_00'
VERSOES = [
    ('v_S_01_00_00', 'Versão S-1.0'),
    ('v_S_01_01_00', 'Versão S-1.1'),
    ('v_S_01_02_00', 'Versão S-1.2'),
    ('v_S_01_03_00', 'Versão S-1.3'),
]

ARQUIVO_GERADO_PELO_SISTEMA = 0
ARQUIVO_IMPORTADO = 1

ARQUIVO_FONTE = [
    (ARQUIVO_GERADO_PELO_SISTEMA, 'Gerado pelo sistema'),
    (ARQUIVO_IMPORTADO, 'Importado'),
]

EVENTO_ORIGEM_SISTEMA = 0
EVENTO_ORIGEM_API = 1

EVENTO_ORIGEM = [
    (EVENTO_ORIGEM_SISTEMA, 'Sistema'),
    (EVENTO_ORIGEM_API, 'Api'),
]

EVENTO_COD = {
    's1000': {'codigo': 'evtInfoEmpregador'},
    's1005': {'codigo': 'evtTabEstab'},
    's1010': {'codigo': 'evtTabRubrica'},
    's1020': {'codigo': 'evtTabLotacao'},
    's1070': {'codigo': 'evtTabProcesso'},
    's1200': {'codigo': 'evtRemun'},
    's1202': {'codigo': 'evtRmnRPPS'},
    's1207': {'codigo': 'evtBenPrRP'},
    's1210': {'codigo': 'evtPgtos'},
    's1260': {'codigo': 'evtComProd'},
    's1270': {'codigo': 'evtContratAvNP'},
    's1280': {'codigo': 'evtInfoComplPer'},
    's1298': {'codigo': 'evtReabreEvPer'},
    's1299': {'codigo': 'evtFechaEvPer'},
    's2190': {'codigo': 'evtAdmPrelim'},
    's2200': {'codigo': 'evtAdmissao'},
    's2205': {'codigo': 'evtAltCadastral'},
    's2206': {'codigo': 'evtAltContratual'},
    's2210': {'codigo': 'evtCAT'},
    's2220': {'codigo': 'evtMonit'},
    's2221': {'codigo': 'evtToxic'},
    's2230': {'codigo': 'evtAfastTemp'},
    's2231': {'codigo': 'evtCessao'},
    's2240': {'codigo': 'evtExpRisco'},
    's2298': {'codigo': 'evtReintegr'},
    's2299': {'codigo': 'evtDeslig'},
    's2300': {'codigo': 'evtTSVInicio'},
    's2306': {'codigo': 'evtTSVAltContr'},
    's2399': {'codigo': 'evtTSVTermino'},
    's2400': {'codigo': 'evtCdBenefIn'},
    's2405': {'codigo': 'evtCdBenefAlt'},
    's2410': {'codigo': 'evtCdBenIn'},
    's2416': {'codigo': 'evtCdBenAlt'},
    's2418': {'codigo': 'evtReativBen'},
    's2420': {'codigo': 'evtCdBenTerm'},
    's2500': {'codigo': 'evtProcTrab'},
    's2501': {'codigo': 'evtContProc'},
    's2555': {'codigo': 'evtConsolidContProc'},
    's3000': {'codigo': 'evtExclusao'},
    's3500': {'codigo': 'evtExcProcTrab'},
    's5001': {'codigo': 'evtBasesTrab'},
    's5002': {'codigo': 'evtIrrfBenef'},
    's5003': {'codigo': 'evtBasesFGTS'},
    's5011': {'codigo': 'evtCS'},
    's5012': {'codigo': 'evtIrrf'},
    's5013': {'codigo': 'evtFGTS'},
    's5501': {'codigo': 'evtTribProcTrab'},
    's5503': {'codigo': 'evtFGTSProcTrab'},
    's8200': {'codigo': 'evtAnotJud'},
    's8299': {'codigo': 'evtBaixa'},
}

VERSIONS_CODE: Dict[str, List[str]] = {
    'v_S_01_00_00': [
        's1000', 's1005', 's1010', 's1020', 's1070', 's1200', 's1202', 's1207', 's1210', 's1260',
        's1270', 's1280', 's1298', 's1299', 's2190', 's2200', 's2205', 's2206', 's2210', 's2220',
        's2230', 's2231', 's2240', 's2298', 's2299', 's2300', 's2306', 's2399', 's2400', 's2405',
        's2410', 's2416', 's2418', 's2420', 's3000', 's5001', 's5002', 's5003', 's5011', 's5013',
        's8299', ],
    'v_S_01_01_00': [
        's1000', 's1005', 's1010', 's1020', 's1070', 's1200', 's1202', 's1207', 's1210', 's1260',
        's1270', 's1280', 's1298', 's1299', 's2190', 's2200', 's2205', 's2206', 's2210', 's2220',
        's2230', 's2231', 's2240', 's2298', 's2299', 's2300', 's2306', 's2399', 's2400', 's2405',
        's2410', 's2416', 's2418', 's2420', 's2500', 's2501', 's3000', 's3500', 's5001', 's5002',
        's5003', 's5011', 's5012', 's5013', 's5501', 's8299', ],
    'v_S_01_02_00': [
        's1000', 's1005', 's1010', 's1020', 's1070', 's1200', 's1202', 's1207', 's1210', 's1260',
        's1270', 's1280', 's1298', 's1299', 's2190', 's2200', 's2205', 's2206', 's2210', 's2220',
        's2230', 's2231', 's2240', 's2298', 's2299', 's2300', 's2306', 's2399', 's2400', 's2405',
        's2410', 's2416', 's2418', 's2420', 's2500', 's2501', 's3000', 's3500', 's5001', 's5002',
        's5003', 's5011', 's5012', 's5013', 's5501', 's5503', 's8200', 's8299', ],
    'v_S_01_03_00': [
        's1000', 's1005', 's1010', 's1020', 's1070', 's1200', 's1202', 's1207', 's1210', 's1260',
        's1270', 's1280', 's1298', 's1299', 's2190', 's2200', 's2205', 's2206', 's2210', 's2220',
        's2221', 's2230', 's2231', 's2240', 's2298', 's2299', 's2300', 's2306', 's2399', 's2400',
        's2405', 's2410', 's2416', 's2418', 's2420', 's2500', 's2501', 's2555', 's3000', 's3500',
        's5001', 's5002', 's5003', 's5011', 's5012', 's5013', 's5501', 's5503', 's8200', 's8299', ],
}

EVENTOS = [
    ('s1000', 'S-1000 - Informações do Empregador/Contribuinte/Órgão Público'),
    ('s1005', 'S-1005 - Tabela de Estabelecimentos, Obras ou Unidades de Órgãos Públicos'),
    ('s1010', 'S-1010 - Tabela de Rubricas'),
    ('s1020', 'S-1020 - Tabela de Lotações Tributárias'),
    ('s1070', 'S-1070 - Tabela de Processos Administrativos/Judiciais'),
    ('s1200', 'S-1200 - Remuneração de Trabalhador vinculado ao Regime Geral de Previd. Social'),
    ('s1202', 'S-1202 - Remuneração de Servidor vinculado ao Regime Próprio de Previd. Social'),
    ('s1207', 'S-1207 - Benefícios - Entes Públicos'),
    ('s1210', 'S-1210 - Pagamentos de Rendimentos do Trabalho'),
    ('s1260', 'S-1260 - Comercialização da Produção Rural Pessoa Física'),
    ('s1270', 'S-1270 - Contratação de Trabalhadores Avulsos Não Portuários'),
    ('s1280', 'S-1280 - Informações Complementares aos Eventos Periódicos'),
    ('s1298', 'S-1298 - Reabertura dos Eventos Periódicos'),
    ('s1299', 'S-1299 - Fechamento dos Eventos Periódicos'),
    ('s2190', 'S-2190 - Registro Preliminar de Trabalhador'),
    ('s2200', 'S-2200 - Cadastramento Inicial do Vínculo e Admissão/Ingresso de Trabalhador'),
    ('s2205', 'S-2205 - Alteração de Dados Cadastrais do Trabalhador'),
    ('s2206', 'S-2206 - Alteração de Contrato de Trabalho/Relação Estatutária'),
    ('s2210', 'S-2210 - Comunicação de Acidente de Trabalho'),
    ('s2220', 'S-2220 - Monitoramento da Saúde do Trabalhador'),
    ('s2221', 'S-2221 - Exame Toxicológico do Motorista Profissional Empregado'),
    ('s2230', 'S-2230 - Afastamento Temporário'),
    ('s2231', 'S-2231 - Cessão/Exercício em Outro Órgão'),
    ('s2240', 'S-2240 - Condições Ambientais do Trabalho - Agentes Nocivos'),
    ('s2298', 'S-2298 - Reintegração/Outros Provimentos'),
    ('s2299', 'S-2299 - Desligamento'),
    ('s2300', 'S-2300 - Trabalhador Sem Vínculo de Emprego/Estatutário - Início'),
    ('s2306', 'S-2306 - Trabalhador Sem Vínculo de Emprego/Estatutário - Alteração Contratual'),
    ('s2399', 'S-2399 - Trabalhador Sem Vínculo de Emprego/Estatutário - Término'),
    ('s2400', 'S-2400 - Cadastro de Beneficiário - Entes Públicos - Início'),
    ('s2405', 'S-2405 - Cadastro de Beneficiário - Entes Públicos - Alteração'),
    ('s2410', 'S-2410 - Cadastro de Benefício - Entes Públicos - Início'),
    ('s2416', 'S-2416 - Cadastro de Benefício - Entes Públicos - Alteração'),
    ('s2418', 'S-2418 - Reativação de Benefício - Entes Públicos'),
    ('s2420', 'S-2420 - Cadastro de Benefício - Entes Públicos - Término'),
    ('s2500', 'S-2500 - Processo Trabalhista'),
    ('s2501', 'S-2501 - Informações de Tributos Decorrentes de Processo Trabalhista'),
    ('s2555',
     'S-2555 - Solicitação de Consolidação das Informações de Tributos '
     'Decorrentes de Processo Trabalhista'),
    ('s3000', 'S-3000 - Exclusão de Eventos'),
    ('s3500', 'S-3500 - Exclusão de Eventos - Processo Trabalhista'),
    ('s5003', 'S-5003 - Informações do FGTS por Trabalhador'),
    ('s5013', 'S-5013 - Informações do FGTS Consolidadas por Contribuinte'),
    ('s5501', 'S-5501 - Informações Consolidadas de Tributos Decorrentes de Processo Trabalhista'),
    ('s5503', 'S-5503 - Informações do FGTS por Trabalhador em Processo Trabalhista'),
    ('s8200', 'S-8200 - Anotação Judicial do Vínculo'),
    ('s8299', 'S-8299 - Baixa Judicial do Vínculo'),
]

SERVICO_ENVIAR = 1
SERVICO_CONSULTAR = 2

SERVICOS = (
    (SERVICO_ENVIAR, 'WsEnviarLoteEventos'),
    (SERVICO_CONSULTAR, 'WsConsultarLoteEventos'),
)

CODIGO_AGUARDANDO_PROCESSAMENTO = '101'

CODIGOS_RESPOSTA_PROCESSADOS = [
    '201', '202']

CODIGOS_RESPOSTA_ERROS = [
    '301', '401', '402', '403', '404', '405', '501', '502', '503', '504', '505']

ARQUIVO_TIPO_HEADER = 1
ARQUIVO_TIPO_REQUEST = 2
ARQUIVO_TIPO_RESPONSE = 3

ARQUIVOS_TIPOS = (
    (ARQUIVO_TIPO_HEADER, 'Header'),
    (ARQUIVO_TIPO_REQUEST, 'Request'),
    (ARQUIVO_TIPO_RESPONSE, 'Response'),
)

ESTADOS = [
    ('AC', 'Acre'),
    ('AL', 'Alagoas'),
    ('AM', 'Amazonas'),
    ('AP', 'Amapá'),
    ('BA', 'Bahia'),
    ('CE', 'Ceará'),
    ('DF', 'Distrito Federal'),
    ('ES', 'Espírito Santo'),
    ('GO', 'Goiás'),
    ('MA', 'Maranhão'),
    ('MG', 'Minas Gerais'),
    ('MS', 'Mato Grosso do Sul'),
    ('MT', 'Mato Grosso'),
    ('PA', 'Pará'),
    ('PB', 'Paraíba'),
    ('PE', 'Pernambuco'),
    ('PI', 'Piauí'),
    ('PR', 'Paraná'),
    ('RJ', 'Rio de Janeiro'),
    ('RN', 'Rio Grande do Norte'),
    ('RO', 'Rondônia'),
    ('RR', 'Roraima'),
    ('RS', 'Rio Grande do Sul'),
    ('SC', 'Santa Catarina'),
    ('SE', 'Sergipe'),
    ('SP', 'São Paulo'),
    ('TO', 'Tocantins'),
]

OPERACOES = [
    (1, 'Incluir'),
    (2, 'Alterar'),
    (3, 'Excluir'),
]

NAO = 0
SIM = 1
SIM_NAO = [
    (NAO, 'Não'),
    (SIM, 'Sim'),
]

TIPO_INSCRICAO_CNPJ_LABEL = '1 - CNPJ'
TIPO_INSCRICAO_CPF_LABEL = '2 - CPF'

CHOICES_INSCRICOESTIPOS = [
    (1, TIPO_INSCRICAO_CNPJ_LABEL),
    (2, TIPO_INSCRICAO_CPF_LABEL),
    (3, '3 - CAEPF (Cadastro de Atividade Econômica de Pessoa Física)'),
    (4, '4 - CNO (Cadastro Nacional de Obra)'),
    (5, '5 - CGC'),
    (6, '6 - CEI'),
]

CHOICES_PROCEMI = [
    (1, '1 - Aplicativo do empregador'),
    (2, '2 - Aplicativo governamental - Empregador Doméstico'),
    (3, '3 - Aplicativo governamental - Web Geral'),
    (4, '4 - Aplicativo governamental - Simplificado Pessoa Jurídica'),
    (5, '5 - Aplicativo governamental - Segurado Especial.'),
]

CHOICES_TPAMB = [
    (1, '1 - Produção'),
    (2, '2 - Produção restrita.'),
]

TPINSC_TRANSMISSOR_EVENTOS = (
    ('1', TIPO_INSCRICAO_CNPJ_LABEL),
    ('2', TIPO_INSCRICAO_CPF_LABEL),
    ('3', '3 - CAEPF (Cadastro de Atividade Econômica de Pessoa Física)'),
    ('4', '4 - CNO (Cadastro Nacional de Obra)'),
)

TIPO_TRANSMISSOR_EVENTOS = (
    ('', ''),
    ('efdreinf', 'EFD-Reinf'),
)

CODIGO_RESPOSTA = [
    (0, 'Cadastrado'),
    (101, '101 - Lote Aguardando Processamento'),
    (201, '201 - Lote Processado com Sucesso'),
    (202, '202 - Lote Processado com Advertências'),
    (301, '301 - Erro Servidor '),
    (401, '401 - Lote Incorreto - Erro preenchimento'),
    (402, '402 - Lote Incorreto - schema Inválido'),
    (403, '403 - Lote Incorreto - Versão do Schema não permitida'),
    (404, '404 - Lote Incorreto - Erro Certificado'),
    (405, '405 - Lote Incorreto - Lote nulo ou vazio'),
    (501, '501 - Solicitação de Consulta Incorreta - Erro Preenchimento'),
    (502, '502 - Solicitação de Consulta Incorreta - Schema Inválido.'),
    (503, '503 - Solicitação de Consulta Incorreta - Versão do Schema Não Permitida.'),
    (504, '504 - Solicitação de Consulta Incorreta - Erro Certificado.'),
    (505, '505 - Solicitação de Consulta Incorreta - Consulta nula ou vazia.'),
]

CODIGO_STATUS_EFDREINF = [
    (0, '0 - Sucesso'),
    (1, '1 - Erro'),
    (2, '2 - Em Processamento'),
]

IMPORTACAO_STATUS = [
    (0, 'Aguardando'),
    (1, 'Processando'),
    (2, 'Processado com sucesso'),
    (3, 'Erro - Processamento'),
    (4, 'Erro - Outros'),
    (5, 'Erro - Arquivo Inválido'),
    (6, 'Erro - Identidade já existente'),
    (7, 'Erro - Versão de leiaute incompatível'),
    (8, 'Erro - Validação de Leiaute'),
]

TIPO_INSCRICAO = [
    (1, TIPO_INSCRICAO_CNPJ_LABEL),
    (2, TIPO_INSCRICAO_CPF_LABEL),
]
