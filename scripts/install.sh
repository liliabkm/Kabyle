#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PROJECT_ROOT="$PWD"
if [[ ! -d .venv ]]; then uv venv .venv; fi
uv pip sync --python .venv/bin/python backend/requirements.lock
npm ci --prefix frontend --no-audit --no-fund
if [[ ! -f .env ]]; then
  .venv/bin/python - <<'ENV'
from pathlib import Path
import secrets,os
p=Path('.env')
fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
with os.fdopen(fd,'w') as f:
    f.write('DATABASE_URL=postgresql+psycopg://kabyle:kabyle_local@127.0.0.1:5432/kabyle\nADMIN_TOKEN='+secrets.token_hex(32)+'\nMEDIA_ROOT=./media\n')
ENV
fi
set -a
source .env
set +a
bash scripts/db.sh
cd backend
"$PROJECT_ROOT/.venv/bin/alembic" upgrade head
"$PROJECT_ROOT/.venv/bin/python" seed.py
cd ../frontend
NEXT_TELEMETRY_DISABLED=1 npm run build
