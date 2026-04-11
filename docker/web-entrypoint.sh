#!/bin/sh
set -eu

cd /app

python /usr/local/bin/wait-for-db.py

python manage.py migrate --noinput
python manage.py collectstatic --no-input
python manage.py create_superuser_if_none

exec gunicorn --bind 0.0.0.0:8000 --workers "${GUNICORN_WORKERS:-3}" config.wsgi:application
