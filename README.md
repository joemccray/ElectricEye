# Jules Just-Works Pack (Extended, Agentic-ready)

This repo is bootstrapped for deterministic Jules runs **and** agentic AI coding done right:
- SFX preflight + manifest integrity
- Reference docs sync (your canonical MD guides)
- Standards enforcement (DRF auth, static/WhiteNoise, Procfile, healthz, Celery skeleton)
- **Architecture-first rails**: PRD, ADRs, Task templates and ADR checks
- **Types + Tests first**: mypy + django-stubs, pytest, coverage gate
- **Event-driven jobs**: a minimal `jobs` app + Celery wiring
- **Safety**: prod/staging guard, destructive-cmd scanner
- **Agent prompts**: information-dense templates (ADD/UPDATE/DELETE/ADD TEST)

## Quickstart
```bash
bash scripts/jules_preamble.sh
python scripts/verify_manifest.py --check
python scripts/adr_add.py "Initial architecture"
pre-commit install
```
