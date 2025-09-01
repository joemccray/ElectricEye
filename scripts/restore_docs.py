#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DOCS.mkdir(parents=True, exist_ok=True)
defaults = {
    "Agentic-Django-Plan.md": "# Plan (placeholder)\n",
    "AGENTS.md": "# Agents (placeholder)\n",
}
for name, content in defaults.items():
    p = DOCS / name
    if not p.exists():
        p.write_text(content, encoding="utf-8")
        print("[restore_docs] created", p)
print("[restore_docs] ok")
