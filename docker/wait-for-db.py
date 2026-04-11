#!/usr/bin/env python3
import os
import sys
import time

import psycopg2


def main():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL não definida.", file=sys.stderr)
        return 1

    attempts = int(os.environ.get("DB_WAIT_ATTEMPTS", "60"))
    delay_seconds = float(os.environ.get("DB_WAIT_DELAY_SECONDS", "2"))

    for attempt in range(1, attempts + 1):
        try:
            connection = psycopg2.connect(database_url)
            connection.close()
            print("Banco de dados disponível.")
            return 0
        except psycopg2.OperationalError as exc:
            print(
                f"Aguardando banco de dados ({attempt}/{attempts}): {exc}",
                file=sys.stderr,
            )
            time.sleep(delay_seconds)

    print("Banco de dados indisponível após o tempo limite.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
