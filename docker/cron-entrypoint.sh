#!/bin/sh
set -eu

cd /app

python /usr/local/bin/wait-for-db.py

until python manage.py shell -c "from django.contrib.auth import get_user_model; get_user_model().objects.exists()" >/dev/null 2>&1; do
    echo "Aguardando migrations serem aplicadas..."
    sleep 2
done

python - <<'PY'
import os
import shlex

with open("/etc/emensageria-cron-env.sh", "w", encoding="utf-8") as env_file:
    env_file.write("#!/bin/sh\n")
    for key, value in sorted(os.environ.items()):
        env_file.write(f"export {key}={shlex.quote(value)}\n")
PY

chmod 600 /etc/emensageria-cron-env.sh

cat <<'EOF' >/etc/cron.d/emensageria
SHELL=/bin/sh
PATH=/opt/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
* * * * * root /usr/local/bin/cron-run.sh >> /proc/1/fd/1 2>> /proc/1/fd/2
EOF

chmod 0644 /etc/cron.d/emensageria

exec cron -f
