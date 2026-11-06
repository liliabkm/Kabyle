#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv-chat
.venv-chat/bin/python -m pip install --upgrade pip
.venv-chat/bin/python -m pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu
.venv-chat/bin/python -m pip install -r training/runtime-requirements.txt
