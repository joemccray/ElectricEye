#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"
if [[ ! -f "scripts/jules_preamble.sh" ]] || [[ ! -f "docs/Agentic-Django-Plan.md" ]] ; then
  if [[ -f "./jules-pack-clean.sfx.sh" ]] ; then chmod +x ./jules-pack-clean.sfx.sh; bash ./jules-pack-clean.sfx.sh .; fi
fi
bash scripts/jules_preamble.sh
echo "[apply_pack] OK"
