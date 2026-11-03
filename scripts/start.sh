#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PROJECT_ROOT="$PWD"
if [[ ! -f .env || ! -f frontend/.next/BUILD_ID ]]; then
  echo 'Run bash scripts/install.sh first.' >&2; exit 1
fi
set -a
source .env
set +a
echo "Démarrage de PostgreSQL…"
bash scripts/db.sh
# Reapply idempotent initialization if the local database volume is new.
echo "Mise à jour de la base et du classement…"
(cd backend && "$PROJECT_ROOT/.venv/bin/alembic" upgrade head && "$PROJECT_ROOT/.venv/bin/python" -u seed.py)
echo "Lancement du site…"
mkdir -p artifacts
(cd backend && exec "$PROJECT_ROOT/.venv/bin/uvicorn" app.main:app --host 127.0.0.1 --port 8000) >artifacts/api.log 2>&1 &
API_PID=$!
(cd frontend && exec node node_modules/next/dist/bin/next start --hostname 0.0.0.0 --port 3000) >artifacts/web.log 2>&1 &
WEB_PID=$!
trap 'kill "$API_PID" "$WEB_PID" 2>/dev/null || true' EXIT INT TERM
for i in {1..30}; do
  if curl --silent --fail http://127.0.0.1:3000/api/health >/dev/null; then
    echo 'Application démarrée. API PostgreSQL vérifiée. Ports : web 3000, API 8000.'
    wait -n "$API_PID" "$WEB_PID"
    exit 1
  fi
  if ! kill -0 "$API_PID" 2>/dev/null || ! kill -0 "$WEB_PID" 2>/dev/null; then
    echo 'Startup failed. Inspect artifacts/api.log and artifacts/web.log.' >&2; exit 1
  fi
  sleep 1
done
echo 'Application readiness timeout; inspect artifacts/*.log.' >&2
exit 1
