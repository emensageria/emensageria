# eMensageria OpenSource

eMensageria - Sistema de Mensageria do eSocial <www.emensageria.com.br>

**ATENÇÃO: O eMensageria opensource contém apenas arquivos para a edição de eventos iniciais do eSocial.**

## Versões eMensageria

- 1.0 (eSocial versão S-1.0 - Leiautes (cons. até NT 01/2021))
- 1.1 (eSocial versão S-1.0 - Leiautes (cons. até NT 02/2021))
- 1.2 (eSocial versão S-1.0 - Leiautes (cons. até NT 03/2021))
- 1.3 (eSocial versão S-1.0 - Leiautes (cons. até NT 04/2021))
- 1.4 (eSocial versão S-1.0 - Leiautes (cons. até NT 05/2022))
- 1.5 (eSocial S-1.0 (até NT 06/2022) e S-1.1 (Beta - 28/07/2022))
- 1.6 (eSocial S-1.0 (até NT 06/2022), S-1.1 (até NT 02/2023) e S-1.2)
- 1.7 (eSocial S-1.0 (até NT 06/2022), S-1.1 (até NT 02/2023) e S-1.2 (até NT 02/2024))
- 1.8 (eSocial S-1.0, S-1.1, S-1.2, e S-1.3)

## Versões compatíveis do eSocial

- S 1.0
- S 1.1
- S 1.2
- S 1.3

## Requisitos de Sistema

- Ubuntu 24.10 x64;
- Python (versão 3.12.7);
- Django (versão 4.2.17);
- Postgres 16;
- outros requisitos no arquivo requirements.txt
- cURL
  - Esta biblioteca é nativa do Linux/Mac, para quem instalar o sistema em servidor Windows é necessário instalar a biblioteca e configurar a variável CURL_PATH no arquivo 'config/.env'. Link da biblioteca para download: https://curl.se/download.html

## Instalação em ambiente em ambiente de desenvolvimento
PASSO-A-PASSO SIMPLIFICADO, EXIGE CONHECIMENTOS TÉCNICOS.

- Crie o banco de dados em postgres:
```
host: localhost
name: emensageria
user: postgres
pass: postgres
port: 5432
```
- Faça o clone do repositório
```
git clone https://github.com/marcelomdevasconcellos/emensageria.git
```
- Crie e ative a virtualenv
```
python3 -m venv venv_emensageria
source venv_emensageria/bin/activate
```
- Acesse a pasta do repositório
```
cd emensageria
```
- Instale os requirements
```
pip install -r requirements.txt
```
- Inclua e edite as variáveis
```
cp config/.env_example config/.env
nano config/.env
```
- Altere as variáveis de acordo com seu ambiente: veja o arquivo no endereço https://github.com/marcelomdevasconcellos/emensageria/blob/main/config/.env_example
- Para rodar a análise do SonarQube usando o token salvo em `config/.env`, configure `SONAR_TOKEN` e execute:
```
./run_sonar.sh
```
- Crie as tabelas no banco de dados
```
python manage.py migrate
```
- Crie do super usuário
```
python manage.py createsuperuser
```
- Acesse o sistema
```
http://localhost:8000/
```

O resto é configurações pelo sistema. Siga a sequência:

1. Certificado
2. Transmissor
3. Eventos ...

## How to generate docker images and deploy locally

We will show you how to generate docker images and deploy the docker container locally. 

To build the application and generate docker images you have to execute the command bellow. Execute from root folder (/log).

```
docker-compose build
```

To deploy the application locally, you have to have execute following command:

```
docker-compose up -d
```

*Tip: if you are in Windows, open a Powershell prompt to run Docker. Do not run inside VS Code prompt because it does not manage memory very well.*

It will set up the docker container from docker image and create the volumes to store application database and data files.

After, we install static artifacts in application. For this, execute:

```
docker-compose exec app python3 manage.py collectstatic --noinput
```

Usually we use the user *admin* and the password as well *admin* in development environment, for tests purposes only. The email field we let empty.
*Please, do not use this in production.*

```
docker-compose exec app python3 manage.py createsuperuser
```

After, we create the database:

```
docker-compose exec app psql -U postgres -h db -c 'CREATE DATABASE emensageria;'
```

After, we apply the database structure:

```
docker-compose exec app python3 manage.py migrate
```

## APIs

#### Atenção: O apache deverá estar configurado para passar o headers para o Django, para isso inclua a configuração abaixo no servidor de produção.

```
WSGIPassAuthorization On
```

#### Gerar token via GET:
- URL: http://localhost:8000/api-token-auth/
- Exemplo CURL (gerando token via requisição GET):
```
curl --data "username=admin&password=admin"
http://localhost:8000/api-token-auth/?format=json
```

- Exemplo CURL (gerando token via requisição REST):
```
curl -d '{"username":"admin", "password":"admin"}' -H "Content-Type:
application/json" -X POST http://localhost:8000/api-token-auth/?format=json
```

#### Consulta de eventos
- URL: http://localhost:8000/esocial/api/eventos/
- Metódos: 'get', 'put', 'patch', 'post', 'head'
- Exemplo CURL:
```
curl -X GET http://localhost:8000/esocial/api/eventos/?format=json -H
'Authorization: Token <token>'
```
- Filtros:
```
http://localhost:8000/esocial/api/eventos/?format=json&user_id=1&identidade=ID1346866130001462021062221014900001
```

#### Executando funções nos eventos individualmente ou consultando e alterando
- URL: http://localhost:8000/esocial/api/eventos/<evento_id>/
- Exemplo CURL:
```
curl -X GET http://localhost:8000/esocial/api/eventos/1/?format=json -H
'Authorization: Token <token>'
```
- Funções:
```
http://localhost:8000/esocial/api/eventos/<evento_id>/atualizar-identidade/?format=json
http://localhost:8000/esocial/api/eventos/<evento_id>/abrir-evento-para-edicao/?format=json
http://localhost:8000/esocial/api/eventos/<evento_id>/validar/?format=json
http://localhost:8000/esocial/api/eventos/<evento_id>/enviar/?format=json
http://localhost:8000/esocial/api/eventos/<evento_id>/consultar/?format=json
```

#### Validando eventos em lote
- URL: http://localhost:8000/esocial/validar-eventos/
- Exemplo CURL:
```
curl -X GET http://localhost:8000/esocial/validar-eventos/ -H
'Authorization: Token <token>'
```

#### Enviando eventos para o eSocial em lote
- Inclua esta chamada em uma CRON para que possa ser realizada periodicamente
- URL: http://localhost:8000/esocial/enviar-transmissores/
- Exemplo CURL:
```
curl -X GET http://localhost:8000/esocial/enviar-transmissores/ -H 'Authorization:
Token <token>'
```
- Exemplo em linha de comando:
```
python manage.py esocial_enviar
```


#### Consultando eventos no eSocial em lote
- Inclua esta chamada em uma CRON para que possa ser realizada periodicamente
- URL: http://localhost:8000/esocial/consultar-transmissores/
- Exemplo CURL:
```
curl -X GET http://localhost:8000/esocial/consultar-transmissores/ -H
'Authorization: Token <token>'
```
- Exemplo em linha de comando:
```
python manage.py esocial_consultar
```

## Formato do JSON de importação via API

Para identificação do formato do JSON para importação siga os seguintes passos:

1. Acessar o FrontEnd utilizando o usuário admin;
2. Criar um evento no leiaute que desejar e salvar o evento;
3. Visualizar a edição do evento;
4. O formato do JSON irá aparecer em um campo somente leitura no formulario chamado JSON. 

## Licença AGPL-3

eMensageria - Sistema de Mensageria Opensource do eSocial
Copyright (C) 2021  Marcelo Medeiros de Vasconcellos

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

## Contato

Marcelo Medeiros de Vasconcellos <marcelomdevasconcellos@gmail.com>

Para maiores informações acesse: www.emensageria.com.br
