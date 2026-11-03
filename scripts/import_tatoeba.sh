#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
TATOEBA_PROJECT_ROOT="$PWD"
set -a
source .env
set +a
TATOEBA_PREVIEW=false
for TATOEBA_ARG in "$@"; do
  if [[ "$TATOEBA_ARG" == '--preview' ]]; then TATOEBA_PREVIEW=true; fi
done
if [[ "$TATOEBA_PREVIEW" == false ]]; then
  (cd backend && "$TATOEBA_PROJECT_ROOT/.venv/bin/alembic" upgrade head && "$TATOEBA_PROJECT_ROOT/.venv/bin/python" seed.py)
fi
exec .venv/bin/python scripts/import_tatoeba.py "$@"
