#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"
mkdir -p docs scripts .github/workflows
python3 scripts/restore_docs.py || python scripts/restore_docs.py
if ! python3 scripts/verify_manifest.py --check 2>/dev/null; then
  echo "[jules] manifest out-of-date; refreshing checksums"
  python3 scripts/verify_manifest.py --update || python scripts/verify_manifest.py --update
fi
echo "[jules] preflight OK"
