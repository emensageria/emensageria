#!/bin/sh
set -u

. /etc/emensageria-cron-env.sh

cd /app

timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

status=0

echo "[$(timestamp)] Executando python manage.py esocial_consultar"
if ! python manage.py esocial_consultar; then
    echo "[$(timestamp)] Falha ao executar esocial_consultar" >&2
    status=1
fi

echo "[$(timestamp)] Executando python manage.py esocial_enviar"
if ! python manage.py esocial_enviar; then
    echo "[$(timestamp)] Falha ao executar esocial_enviar" >&2
    status=1
fi

exit "$status"
