#!/usr/bin/env sh
set -e

if [ "$RUN_MIGRATIONS" = "false" ]; then
  exec "$@"
fi

export PYTHONPATH=/app

TRIES=30
SLEEP=2

wait_for_db() {
  python - <<'PY'
import os
import time
import psycopg2

host = os.getenv("POSTGRES_HOST", "db")
port = int(os.getenv("POSTGRES_PORT", "5432"))
user = os.getenv("POSTGRES_USER", "bananapics")
password = os.getenv("POSTGRES_PASSWORD", "bananapics")
dbname = os.getenv("POSTGRES_DB", "bananapics")

conn = psycopg2.connect(
    host=host, port=port, user=user, password=password, dbname=dbname
)
conn.close()
PY
}

for i in $(seq 1 $TRIES); do
  if wait_for_db; then
    break
  fi
  if [ "$i" -eq "$TRIES" ]; then
    echo "DB is not ready after $TRIES attempts" >&2
    exit 1
  fi
  sleep $SLEEP
done

alembic -c /app/alembic.ini upgrade head

exec "$@"
