#!/usr/bin/env bash
set -euo pipefail
if [[ -f "requirements.txt" ]]; then python -m pip install -r requirements.txt || true; fi
if [[ -f "requirements-dev.txt" ]]; then python -m pip install -r requirements-dev.txt || true; fi
ruff check . --fix || true
black . || true
isort . || true
echo "[cleanup] done"
