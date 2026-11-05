#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
TASK_PROJECT_ROOT="$PWD"
set -a
source .env
set +a
bash scripts/db.sh
(cd backend && "$TASK_PROJECT_ROOT/.venv/bin/alembic" upgrade head)
.venv/bin/python -u backend/seed.py
exec .venv/bin/python -u scripts/organize_data.py "$@"
