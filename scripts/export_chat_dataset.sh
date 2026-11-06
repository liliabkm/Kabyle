#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
set -a
source .env
set +a
exec .venv/bin/python -u scripts/export_chat_dataset.py "$@"
