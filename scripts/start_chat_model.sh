#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -x .venv-chat/bin/python ]]; then
  echo 'Lance d’abord bash scripts/install_chat_model.sh'; exit 1
fi
exec .venv-chat/bin/python scripts/serve_chat_model.py "$@"
