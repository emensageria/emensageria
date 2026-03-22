#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$ROOT_DIR/config/.env"
PROJECT_SETTINGS="$ROOT_DIR/sonar-project.properties"
REPORT_TASK_FILE="$ROOT_DIR/.scannerwork/report-task.txt"

read_env_var() {
    local key="$1"

    awk -v key="$key" '
        $0 ~ "^[[:space:]]*" key "=" {
            value = substr($0, index($0, "=") + 1)
            sub(/^[[:space:]]+/, "", value)
            sub(/[[:space:]]+$/, "", value)

            if (value ~ /^".*"$/ || value ~ /^'\''.*'\''$/) {
                value = substr(value, 2, length(value) - 2)
            }

            print value
            exit
        }
    ' "$ENV_FILE"
}

if [[ -f "$ROOT_DIR/.sonarcloud.properties" ]]; then
    PROJECT_SETTINGS="$ROOT_DIR/.sonarcloud.properties"
fi

if [[ ! -f "$ENV_FILE" ]]; then
    echo "Arquivo de ambiente não encontrado: $ENV_FILE"
    exit 1
fi

if ! command -v sonar-scanner >/dev/null 2>&1; then
    echo "Comando sonar-scanner não encontrado no PATH."
    exit 1
fi

SONAR_TOKEN="${SONAR_TOKEN:-$(read_env_var SONAR_TOKEN)}"
if [[ -z "$SONAR_TOKEN" ]]; then
    echo "A variável SONAR_TOKEN não foi configurada em config/.env."
    exit 1
fi

export SONAR_TOKEN

SONAR_HOST_URL="${SONAR_HOST_URL:-$(read_env_var SONAR_HOST_URL)}"
SONAR_PROJECT_KEY="${SONAR_PROJECT_KEY:-$(read_env_var SONAR_PROJECT_KEY)}"

if [[ -f "$REPORT_TASK_FILE" ]]; then
    if [[ -z "$SONAR_HOST_URL" ]]; then
        SONAR_HOST_URL="$(awk -F= '$1 == "serverUrl" {print $2}' "$REPORT_TASK_FILE")"
    fi
    if [[ -z "$SONAR_PROJECT_KEY" ]]; then
        SONAR_PROJECT_KEY="$(awk -F= '$1 == "projectKey" {print $2}' "$REPORT_TASK_FILE")"
    fi
fi

scanner_args=("-Dproject.settings=$PROJECT_SETTINGS")

if [[ -n "$SONAR_HOST_URL" ]]; then
    scanner_args+=("-Dsonar.host.url=$SONAR_HOST_URL")
fi

if [[ -n "$SONAR_PROJECT_KEY" ]] && ! grep -q '^sonar.projectKey=' "$PROJECT_SETTINGS"; then
    scanner_args+=("-Dsonar.projectKey=$SONAR_PROJECT_KEY")
fi

exec sonar-scanner "${scanner_args[@]}" "$@"
