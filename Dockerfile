FROM python:3.12-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv

COPY requirements.txt /app/requirements.txt

RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r /app/requirements.txt

FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/opt/venv/bin:$PATH" \
    LANG=pt_BR.UTF-8 \
    LANGUAGE=pt_BR:pt \
    LC_ALL=pt_BR.UTF-8

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \
    curl \
    graphviz \
    locales \
    wkhtmltopdf \
    && sed -i 's/# pt_BR.UTF-8 UTF-8/pt_BR.UTF-8 UTF-8/' /etc/locale.gen \
    && locale-gen pt_BR.UTF-8 \
    && update-locale LANG=pt_BR.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
COPY docker /opt/docker

RUN chmod +x /opt/docker/*.sh \
    && ln -sf /opt/docker/web-entrypoint.sh /usr/local/bin/web-entrypoint.sh \
    && ln -sf /opt/docker/cron-entrypoint.sh /usr/local/bin/cron-entrypoint.sh \
    && ln -sf /opt/docker/cron-run.sh /usr/local/bin/cron-run.sh \
    && ln -sf /opt/docker/wait-for-db.py /usr/local/bin/wait-for-db.py

COPY . /app

EXPOSE 8000

CMD ["/usr/local/bin/web-entrypoint.sh"]
