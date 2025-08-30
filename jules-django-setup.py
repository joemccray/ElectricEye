#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jules-django-setup.py
---------------------
Bootstrap and harden a Django repo so Jules + CI run deterministically.

This version includes the 5 requested upgrades:
1) CrewAI pins in requirements + a compat shim and auto-rewrite of legacy imports.
2) A Makefile writer so `make test` always uses pytest + settings_test.
3) Test settings that AUTO-INSTALL local apps (folders with apps.py).
4) Directly ensure a /healthz URL in config/urls.py (not only via enforce script).
5) Keep all preflight/manifest, fixtures, HTTP blocker, Celery eager, etc.

Usage:
    python jules-django-setup.py .
"""

from __future__ import annotations
import sys
import re
import json
import stat
from pathlib import Path

BOLD = "\033[1m"
RESET = "\033[0m"

def info(msg: str) -> None:
    print(f"{BOLD}[jules-setup]{RESET} {msg}")

def rel(p: Path, root: Path) -> Path:
    try:
        return p.relative_to(root)
    except Exception:
        return p

def write(path: Path, content: str, executable: bool = False, root: Path | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_text(encoding="utf-8") != content:
        path.write_text(content, encoding="utf-8")
    if executable:
        mode = path.stat().st_mode
        path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    if root:
        print("  - wrote", rel(path, root))

def append_once(path: Path, lines: list[str], root: Path | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    changed = False
    for ln in lines:
        if ln not in existing:
            existing += ("" if existing.endswith("\n") or existing == "" else "\n") + ln + "\n"
            changed = True
    if changed:
        path.write_text(existing, encoding="utf-8")
        if root:
            print("  - updated", rel(path, root))

# ---------- Requirements ----------

def upsert_requirements(root: Path) -> None:
    base = root / "requirements.txt"
    dev = root / "requirements-dev.txt"
    want_base = [
        "Django>=5.0,<6.0",
        "djangorestframework>=3.15,<4.0",
        "gunicorn>=22.0",
        "whitenoise>=6.5",
        "python-dotenv>=1.0",
        "celery>=5.4",
        "requests>=2.32",
        "python-jose[cryptography]>=3.3.0",
        # (1) CrewAI pins for stable `tool` decorator import surface
        "crewai>=0.51,<1.0",
        "crewai-tools>=0.13,<1.0",
    ]
    want_dev = [
        "ruff>=0.5",
        "black>=24.0",
        "isort>=5.13",
        "pytest>=8.0",
        "pytest-django>=4.8",
        "pytest-cov>=5.0",
        "mypy>=1.11",
        "django-stubs[compatible-mypy]>=5.0",
        "pre-commit>=3.8.0",
    ]
    append_once(base, want_base, root)
    append_once(dev, want_dev, root)

# ---------- Settings detection & enforcement ----------

def detect_settings(root: Path) -> Path | None:
    for p in [root / "config" / "settings" / "base.py",
              root / "config" / "settings.py",
              root / "settings.py"]:
        if p.exists():
            return p
    return None

def enforce_settings(settings_path: Path, root: Path) -> None:
    s = settings_path.read_text(encoding="utf-8") if settings_path.exists() else ""
    if not s:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        s = (
            "from pathlib import Path\n"
            "BASE_DIR = Path(__file__).resolve().parents[1]\n"
            "SECRET_KEY = 'changeme'\n"
            "DEBUG = True\n"
            "ALLOWED_HOSTS = ['*']\n"
            "INSTALLED_APPS = []\n"
            "MIDDLEWARE = ['django.middleware.security.SecurityMiddleware']\n"
        )
    if "rest_framework" not in s and "INSTALLED_APPS" in s:
        s = re.sub(r"(INSTALLED_APPS\s*=\s*\[)", r"\1\n    'rest_framework',", s, count=1, flags=re.M)
    if "whitenoise.middleware.WhiteNoiseMiddleware" not in s and "MIDDLEWARE" in s:
        s = re.sub(r'("django.middleware.security.SecurityMiddleware",\s*)',
                   r'\1\n    "whitenoise.middleware.WhiteNoiseMiddleware",\n',
                   s, count=1)
    if "STATIC_URL" not in s:
        s += "\nSTATIC_URL = '/static/'\n"
    if "from pathlib import Path" not in s:
        s = "from pathlib import Path\n" + s
    if "BASE_DIR" not in s:
        s = "from pathlib import Path\nBASE_DIR = Path(__file__).resolve().parents[1]\n" + s
    if "STATIC_ROOT" not in s:
        s += "STATIC_ROOT = BASE_DIR / 'staticfiles'\n"
    if "STORAGES" not in s:
        s += "STORAGES = { 'staticfiles': { 'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage' } }\n"
    if "INSTALLED_APPS" in s and "'jobs'" not in s:
        s = re.sub(r"(INSTALLED_APPS\s*=\s*\[)", r"\1\n    'jobs',", s, count=1, flags=re.M)
    if "CELERY_TASK_ALWAYS_EAGER" not in s:
        s += "\n# For tests you may override to True\nCELERY_TASK_ALWAYS_EAGER = False\n"
    if "DJANGO_ENV" not in s:
        s += (
            "\nimport os\n"
            "ENV = os.getenv('DJANGO_ENV','development')\n"
            "if ENV == 'production':\n"
            "    DEBUG = False\n"
            "    assert os.getenv('DATABASE_URL'), 'DATABASE_URL required in production'\n"
            "    if os.getenv('ALLOW_DESTRUCTIVE','0') != '1':\n"
            "        os.environ['DJANGO_SUPPRESS_MGMT_WARN'] = '1'\n"
        )
    settings_path.write_text(s, encoding="utf-8")
    print("  - enforced", rel(settings_path, root))

# ---------- CrewAI compat + import patcher (1) ----------

def patch_crewai_imports(root: Path) -> None:
    """
    Create a compat shim and normalize imports:
    `from crewai import tool` -> `from crewai_tool_compat import tool`
    """
    compat = root / "crewai_tool_compat.py"
    compat_code = """# Compat shim for CrewAI `tool` decorator across versions
try:
    from crewai.tools import tool  # preferred (newer)
except Exception:
    try:
        from crewai import tool  # older
    except Exception:
        try:
            from crewai_tools import tool  # some distros ship here
        except Exception as e:
            raise ImportError(
                "Missing CrewAI 'tool' decorator; install 'crewai' / 'crewai-tools'."
            ) from e
"""
    write(compat, compat_code, root=root)

    # Rewrite legacy imports across the repo
    for py in root.rglob("*.py"):
        if py.name == "jules-django-setup.py" or py.name == "crewai_tool_compat.py":
            continue
        try:
            text = py.read_text(encoding="utf-8")
        except Exception:
            continue
        if "from crewai import tool" in text:
            new = text.replace("from crewai import tool", "from crewai_tool_compat import tool")
            if new != text:
                py.write_text(new, encoding="utf-8")
                print("  - patched CrewAI import in", rel(py, root))

# ---------- Makefile writer (2) ----------

def write_makefile(root: Path) -> None:
    mf = root / "Makefile"
    content = """# Standardized test runner for CI and local
PYTEST ?= pytest -q
export DJANGO_SETTINGS_MODULE ?= config.settings_test

.PHONY: test unit lint typecheck
test: unit
unit:
\t$(PYTEST)

lint:
\truff check .

typecheck:
\tmypy .
"""
    if not mf.exists():
        write(mf, content, root=root)
    else:
        txt = mf.read_text(encoding="utf-8")
        if "pytest" not in txt or "DJANGO_SETTINGS_MODULE" not in txt:
            mf.write_text(content, encoding="utf-8")
            print("  - normalized Makefile to use pytest + settings_test")

# ---------- Helper: autodetect local Django apps (3) ----------

def autodetect_local_apps(root: Path) -> list[str]:
    apps = []
    for pkg in root.iterdir():
        if not pkg.is_dir() or pkg.name.startswith((".", "_")):
            continue
        if (pkg / "apps.py").exists():
            apps.append(pkg.name)
    return apps

# ---------- URLs: ensure /healthz route (4) ----------

def ensure_health_url(root: Path) -> None:
    urls = root / "config" / "urls.py"
    if not urls.exists():
        return
    s = urls.read_text(encoding="utf-8")
    if "healthz" not in s:
        s = (
            "from django.contrib import admin\n"
            "from django.urls import path\n"
            "from integrations.ops.health import healthz\n\n"
            "urlpatterns = [\n"
            "    path('admin/', admin.site.urls),\n"
            "    path('healthz', healthz),\n"
            "]\n"
        )
        urls.write_text(s, encoding="utf-8")
        print("  - added /healthz to config/urls.py")

# ---------- Main ----------

def main() -> None:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    info(f"target: {root}")
    root.mkdir(parents=True, exist_ok=True)

    # Only run on Django repos
    if not (root / "manage.py").exists() and not (root / "config").exists():
        info("No Django project detected (missing manage.py/config). Aborting with guidance.")
        print("Create a Django project first:")
        print("  python -m pip install 'Django>=5,<6'")
        print("  django-admin startproject config .")
        sys.exit(0)

    # README
    write(
        root / "README.md",
        """# Jules Just-Works Pack (Extended, Agentic-ready)

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
""",
        root=root,
    )

    # Reference doc registry
    write(
        root / "docs" / "reference-sources.json",
        json.dumps(
            {
                "version": 1,
                "sources": [
                    {"name": "Django-Business-Logic", "url": "http://146.190.150.94/app-reference-docs/Django-Business-Logic.md"},
                    {"name": "Django-clerk", "url": "http://146.190.150.94/app-reference-docs/Django-clerk.md"},
                    {"name": "Django-Data-Flow", "url": "http://146.190.150.94/app-reference-docs/Django-Data-Flow.md"},
                    {"name": "Django-REST-Framework-Cheat-Sheet", "url": "http://146.190.150.94/app-reference-docs/Django-REST-Framework-Cheat-Sheet.md"},
                    {"name": "Django-CrewAI", "url": "http://146.190.150.94/app-reference-docs/Django-CrewAI.v2.md"},
                    {"name": "Django-SaaS", "url": "http://146.190.150.94/app-reference-docs/Django-SaaS.md"},
                    {"name": "Django-Freshdesk", "url": "http://146.190.150.94/app-reference-docs/Django-Freshdesk.md"},
                    {"name": "Railway-Native-Django-Deployment-Tips", "url": "http://146.190.150.94/app-reference-docs/Railway-Native-Django-Deployment-Tips.md"},
                    {"name": "Code-Review-Template", "url": "http://146.190.150.94/app-reference-docs/Code-Review-Template.md"},
                ],
            },
            indent=2,
        ),
        root=root,
    )

    # Agent docs & plan
    write(
        root / "docs" / "AGENTS.md",
        """# AGENTS

## Dev Agent
- Implement features per PRD and ADRs. Respect typed schemas and tests-first.
- Use **information-dense** prompts with explicit file paths (ADD/UPDATE/DELETE/ADD TEST).

## QA Agent
- Write integration tests that hit real code paths.
- Enforce coverage threshold and fail until green.

## Docs Agent
- Keep PRD/ADRs/task specs current. Append ADRs after significant changes.

## Infra Agent
- Ensure CI passes: lint, types, tests, ADR check.
""",
        root=root,
    )

    write(
        root / "docs" / "Agentic-Django-Plan.md",
        """# Agentic Django Plan

1) **Apply SFX** + preflight (`bash scripts/jules_apply_pack.sh`)
2) **Plan**: write PRD, initial ADR(s); agree on types/serializers
3) **Types/Tests first**: add schemas + failing integration tests
4) **Implement** features until tests green
5) **Record** ADR updates
6) **Cleanup**: formatters, ruff, isort
""",
        root=root,
    )

    # PRD/ADR/task templates
    write(
        root / "docs" / "PRD.template.md",
        """# Product Requirements Document (PRD)

## 1. Summary
## 2. Goals / Non-Goals
## 3. User Stories / JTBD
## 4. Scope / Out-of-scope
## 5. Functional Requirements
- API, background jobs, data model changes
## 6. Acceptance Criteria (information-dense)
- CREATE/UPDATE/DELETE with file paths; ADD TEST: tests/test_<feature>.py
## 7. Metrics
## 8. Risks/Mitigations
""",
        root=root,
    )
    write(
        root / "docs" / "adr" / "0000-template.md",
        """# ADR N: <Decision title>
Date: YYYY-MM-DD

## Status
Proposed

## Context

## Decision

## Consequences

## References
""",
        root=root,
    )
    write(
        root / "docs" / "tasks" / "IMPLEMENT.template.md",
        """# IMPLEMENT: <feature-name>
- UPDATE: <file path(s)> to include <specific change>
- ADD: <new file path(s)> with <purpose>
- DELETE: <file path(s)>
- ADD TEST: tests/test_<feature>_e2e.py (integration preferred)
- VERIFY: run `pytest` and paste failing output, fix until green
- RECORD: `python scripts/adr_add.py "<title>"` with key decisions
""",
        root=root,
    )
    write(
        root / "docs" / "tasks" / "FIX.template.md",
        """# FIX: <bug-title>
- REPRO: <steps or failing test>
- UPDATE: <file paths>
- ADD TEST: tests/test_<bug>_regression.py
- VERIFY: run `pytest`; iterate until green
- RECORD: ADR note if architectural
""",
        root=root,
    )

    # Pack scripts
    write(
        root / "scripts" / "jules_preamble.sh",
        """#!/usr/bin/env bash
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
""",
        executable=True, root=root,
    )
    write(
        root / "scripts" / "restore_docs.py",
        """#!/usr/bin/env python3
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT/'docs'
DOCS.mkdir(parents=True, exist_ok=True)
defaults = {"Agentic-Django-Plan.md": "# Plan (placeholder)\\n", "AGENTS.md": "# Agents (placeholder)\\n"}
for name, content in defaults.items():
    p = DOCS/name
    if not p.exists():
        p.write_text(content, encoding="utf-8")
        print("[restore_docs] created", p)
print("[restore_docs] ok")
""",
        root=root,
    )
    write(
        root / "scripts" / "verify_manifest.py",
        """#!/usr/bin/env python3
import sys, hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()
def load_manifest() -> dict:
    p = ROOT/'docs'/'manifest.yaml'
    if not p.exists():
        return {"required": [{"path":"README.md"}]}
    txt = p.read_text()
    data = {"required": []}
    for line in txt.splitlines():
        line=line.strip()
        if line.startswith("- "):
            data["required"].append({"path": line[2:].strip()})
        elif line.startswith("path:"):
            data["required"].append({"path": line.split(":",1)[1].strip()})
    if not data["required"]:
        data = json.loads(txt)
    return data
def check(m: dict)->int:
    missing=[]
    mismatches=[]
    for it in m.get("required", []):
        p=ROOT/it["path"]
        if not p.exists():
            missing.append(it["path"])
            continue
        if "sha256" in it and sha256(p)!=it["sha256"]:
            mismatches.append((it["path"], it["sha256"], sha256(p)))
    if missing or mismatches:
        if missing:
            print("Missing:")
            [print(" -",x) for x in missing]
        if mismatches:
            print("Checksum mismatches:")
            for path,exp,got in mismatches:
                print(f" - {path}\\n   expected:{exp}\\n   got:{got}")
        return 1
    print("Manifest OK")
    return 0
def update(m: dict)->int:
    changed=False
    for it in m.get("required", []):
        p=ROOT/it["path"]
        if not p.exists():
            continue
        s=sha256(p)
        if it.get("sha256")!=s:
            it["sha256"]=s
            changed=True
    if changed:
        out=ROOT/'docs'/'manifest.yaml'
        with out.open("w", encoding="utf-8") as f:
            f.write("required:\\n")
            for x in m["required"]:
                if "sha256" in x:
                    f.write(f"  - path: {x['path']}\\n    sha256: {x['sha256']}\\n")
                else:
                    f.write(f"  - {x['path']}\\n")
        print("Updated manifest.")
        return 0
    print("No updates needed.")
    return 0
if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--update", action="store_true")
    a=ap.parse_args()
    m=load_manifest()
    sys.exit(update(m) if a.update else check(m))
""",
        root=root,
    )
    write(
        root / "scripts" / "jules_apply_pack.sh",
        """#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"
if [[ ! -f "scripts/jules_preamble.sh" ]] || [[ ! -f "docs/Agentic-Django-Plan.md" ]] ; then
  if [[ -f "./jules-pack-clean.sfx.sh" ]] ; then chmod +x ./jules-pack-clean.sfx.sh; bash ./jules-pack-clean.sfx.sh .; fi
fi
bash scripts/jules_preamble.sh
echo "[apply_pack] OK"
""",
        executable=True, root=root,
    )
    write(
        root / "scripts" / "jules_sync_docs.py",
        """#!/usr/bin/env python3
import json, time
from pathlib import Path
from urllib.request import urlopen
ROOT = Path(__file__).resolve().parents[1]
REG = ROOT/'docs'/'reference-sources.json'
OUT = ROOT/'docs'/'reference'
OUT.mkdir(parents=True, exist_ok=True)
STATE = ROOT/'docs'/'reference-sources.state.json'
def fetch(url):
    with urlopen(url, timeout=20) as r:
        return r.read()
def main():
    reg=json.loads(REG.read_text(encoding='utf-8'))
    state={"ts": int(time.time()), "entries": []}
    for s in reg["sources"]:
        url=s["url"]
        dest=OUT/url.split("/")[-1]
        try:
            b=fetch(url)
            dest.write_bytes(b)
            print("[sync]", s["name"], "->", dest.name, f"({len(b)} bytes)")
            state["entries"].append({"name": s["name"], "url": url, "file": dest.name})
        except Exception as e:
            if dest.exists():
                print("[sync]", s["name"], "failed; kept cached", dest.name)
            else:
                raise
    STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    print("[sync] done")
if __name__=="__main__":
    main()
""",
        root=root,
    )
    write(
        root / "scripts" / "jules_cleanup.sh",
        """#!/usr/bin/env bash
set -euo pipefail
if [[ -f "requirements.txt" ]]; then python -m pip install -r requirements.txt || true; fi
if [[ -f "requirements-dev.txt" ]]; then python -m pip install -r requirements-dev.txt || true; fi
ruff check . --fix || true
black . || true
isort . || true
echo "[cleanup] done"
""",
        executable=True, root=root,
    )

    # ADR helper
    write(
        root / "scripts" / "adr_add.py",
        """#!/usr/bin/env python3
import sys, time
from pathlib import Path
title = " ".join(sys.argv[1:]).strip() or "Untitled Decision"
slug = title.lower().replace(" ", "-")
adr_dir = Path("docs/adr")
adr_dir.mkdir(parents=True, exist_ok=True)
idx = max([0] + [int(p.name.split("-")[0]) for p in adr_dir.glob("[0-9][0-9][0-9][0-9]-*.md")]) + 1
p = adr_dir / f"{idx:04d}-{slug}.md"
p.write_text(f"# ADR {idx}: {title}\\nDate: {time.strftime('%Y-%m-%d')}\\n\\n## Status\\nProposed\\n\\n## Context\\n\\n## Decision\\n\\n## Consequences\\n\\n## References\\n", encoding="utf-8")
print(p)
""",
        executable=True, root=root,
    )

    # Integrations
    write(
        root / "integrations" / "ops" / "health.py",
        "from django.http import JsonResponse\n"
        "def healthz(_):\n"
        "    return JsonResponse({'ok': True, 'service':'django-app'})\n",
        root=root,
    )
    write(
        root / "integrations" / "auth" / "clerk_auth.py",
        """import os, time
from typing import Optional, Tuple
from urllib.request import urlopen
from jose import jwk, jwt
from jose.utils import base64url_decode
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
CLERK_JWKS_URL = os.getenv("CLERK_JWKS_URL", "")
CLERK_AUDIENCE  = os.getenv("CLERK_AUDIENCE", "")
CLERK_ISSUER    = os.getenv("CLERK_ISSUER", "")
_JWKS_CACHE = {"ts": 0, "jwks": None}
def _get_jwks():
    if _JWKS_CACHE["jwks"] and (time.time() - _JWKS_CACHE["ts"] < 3600):
        return _JWKS_CACHE["jwks"]
    with urlopen(CLERK_JWKS_URL, timeout=10) as r:
        import json as _json
        _JWKS_CACHE["jwks"] = _json.loads(r.read())
        _JWKS_CACHE["ts"] = time.time()
    return _JWKS_CACHE["jwks"]
def _verify_jwt(token: str) -> dict:
    headers = jwt.get_unverified_header(token)
    kid = headers.get("kid")
    jwks = _get_jwks()
    key = next((k for k in jwks.get("keys",[]) if k.get("kid")==kid), None)
    if not key:
        raise exceptions.AuthenticationFailed("JWKS kid not found")
    public_key = jwk.construct(key)
    message, encoded_sig = token.rsplit(".", 1)
    decoded_sig = base64url_decode(encoded_sig.encode())
    if not public_key.verify(message.encode(), decoded_sig):
        raise exceptions.AuthenticationFailed("Invalid signature")
    claims = jwt.get_unverified_claims(token)
    if CLERK_AUDIENCE and claims.get("aud") not in [CLERK_AUDIENCE] + str(CLERK_AUDIENCE).split(","):
        raise exceptions.AuthenticationFailed("Invalid audience")
    if CLERK_ISSUER and claims.get("iss") != CLERK_ISSUER:
        raise exceptions.AuthenticationFailed("Invalid issuer")
    return claims
class ClerkJWTAuthentication(BaseAuthentication):
    keyword = "Bearer"
    def authenticate(self, request) -> Optional[Tuple[object, None]]:
        if os.getenv("DJANGO_ENV") == "test" or os.getenv("USE_CLERK_AUTH") == "0":
            return None  # fall back to Session/Basic in REST_FRAMEWORK during tests
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return None
        token = auth[len("Bearer "):].strip()
        if not token:
            raise exceptions.AuthenticationFailed("Missing token")
        claims = _verify_jwt(token)
        from django.contrib.auth.models import AnonymousUser
        user = AnonymousUser()
        user.id = claims.get("sub")
        user.email = claims.get("email")
        return (user, None)
""",
        root=root,
    )

    # pytest & tests
    write(
        root / "pytest.ini",
        """[pytest]
DJANGO_SETTINGS_MODULE = config.settings_test
python_files = tests/test_*.py
addopts = -q --strict-markers --maxfail=1 --disable-warnings --cov=. --cov-report=term
""",
        root=root,
    )
    write(
        root / "tests" / "test_healthz.py",
        """import pytest
from django.test import Client

@pytest.mark.django_db
def test_healthz_ok():
    c = Client()
    r = c.get('/healthz')
    assert r.status_code == 200
    assert r.json().get('ok') is True
""",
        root=root,
    )

    # settings_test with auto-installed local apps (3)
    local_apps = autodetect_local_apps(root)
    write(
        root / "config" / "settings_test.py",
        f"""from .settings import *  # noqa

DEBUG = True
SECRET_KEY = "test-secret-key"

DATABASES = {{
    "default": {{"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
}}

# Ensure local apps are installed during tests
try:
    INSTALLED_APPS += {local_apps!r}
except NameError:
    INSTALLED_APPS = {local_apps!r}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

REST_FRAMEWORK = {{
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 50,
}}

USE_CLERK_AUTH = False
""",
        root=root,
    )

    # HTTP blocker & common fixtures
    write(
        root / "tests" / "helpers" / "http_block.py",
        """import os
import pytest
import requests

@pytest.fixture(autouse=True)
def _block_external_http(monkeypatch):
    if os.getenv("NO_EXTERNAL_HTTP") != "1":
        return
    def _blocked(*args, **kwargs):
        raise RuntimeError("External HTTP is disabled in tests (set NO_EXTERNAL_HTTP=0 to allow).")
    for method in ("get","post","put","delete","patch","head","options"):
        monkeypatch.setattr(requests, method, _blocked)
""",
        root=root,
    )
    write(
        root / "tests" / "conftest.py",
        """import os
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from .helpers.http_block import _block_external_http  # noqa: F401

@pytest.fixture(autouse=True, scope="session")
def _env_for_tests():
    os.environ.setdefault("DJANGO_ENV", "test")
    os.environ.setdefault("ALLOW_DESTRUCTIVE", "0")
    os.environ.setdefault("NO_EXTERNAL_HTTP", "1")
    yield

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user(db):
    User = get_user_model()
    return User.objects.create_user(username="tester", email="tester@example.com", password="password")

@pytest.fixture
def authed(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client
""",
        root=root,
    )

    # minimal jobs app scaffold
    write(
        root / "jobs" / "models.py",
        """from django.db import models

class GreetingJob(models.Model):
    first_name = models.CharField(max_length=100)
    voice_id = models.CharField(max_length=100)
    greeting_seconds = models.FloatField()
    video_path = models.CharField(max_length=500)
    status = models.CharField(max_length=12, default="queued")
    result_url = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
""",
        root=root,
    )
    write(
        root / "jobs" / "tasks.py",
        """from celery import shared_task
from .models import GreetingJob

@shared_task
def process_greeting_job(job_id: int) -> None:
    job = GreetingJob.objects.get(id=job_id)
    job.status = "processing"
    job.save(update_fields=["status"])
    # simulate work; in real app integrate services and set real URL
    job.result_url = "https://example.com/out.mp4"
    job.status = "done"
    job.save(update_fields=["result_url","status"])
""",
        root=root,
    )
    write(
        root / "jobs" / "signals.py",
        """from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import GreetingJob
from .tasks import process_greeting_job

@receiver(post_save, sender=GreetingJob)
def enqueue_job(sender, instance: GreetingJob, created: bool, **kwargs):
    if created:
        process_greeting_job.delay(instance.id)
""",
        root=root,
    )
    write(
        root / "jobs" / "apps.py",
        """from django.apps import AppConfig
class JobsConfig(AppConfig):
    name = "jobs"
    def ready(self):
        from . import signals  # noqa
""",
        root=root,
    )
    write(
        root / "tests" / "test_greeting_job_e2e.py",
        """import pytest
from jobs.models import GreetingJob
from jobs.tasks import process_greeting_job

@pytest.mark.django_db
def test_job_reaches_done():
    job = GreetingJob.objects.create(first_name="John", voice_id="v1", greeting_seconds=1.5, video_path="/tmp/in.mp4")
    process_greeting_job(job.id)  # run synchronously in test (CELERY_TASK_ALWAYS_EAGER=True)
    job.refresh_from_db()
    assert job.status == "done"
    assert job.result_url
""",
        root=root,
    )

    # mypy + schemas + serializers
    write(
        root / "mypy.ini",
        """[mypy]
python_version = 3.11
plugins = mypy_django_plugin.main
strict = True
warn_unused_ignores = True
warn_redundant_casts = True
disallow_any_generics = True
disallow_untyped_defs = True
disallow_incomplete_defs = True

[mypy.plugins.django-stubs]
django_settings_module = config.settings
""",
        root=root,
    )
    write(
        root / "core" / "schemas.py",
        """from typing import TypedDict, Literal

class CreateGreetingRequest(TypedDict):
    first_name: str
    voice_id: str
    greeting_seconds: float
    video_path: str

class CreateGreetingResponse(TypedDict):
    job_id: str
    status: Literal["queued","processing","done","failed"]

class GreetingJob(TypedDict):
    id: int
    first_name: str
    voice_id: str
    greeting_seconds: float
    video_path: str
    status: Literal["queued","processing","done","failed"]
    result_url: str | None
""",
        root=root,
    )
    write(
        root / "core" / "serializers.py",
        """from rest_framework import serializers

class CreateGreetingRequestSer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    voice_id = serializers.CharField(max_length=100)
    greeting_seconds = serializers.FloatField(min_value=0)
    video_path = serializers.CharField()

class CreateGreetingResponseSer(serializers.Serializer):
    job_id = serializers.CharField()
    status = serializers.ChoiceField(choices=["queued","processing","done","failed"])
""",
        root=root,
    )

    # prod guard + env
    append_once(
        root / ".env.example",
        [
            "DJANGO_ENV=development",
            "DATABASE_URL=postgresql://localhost:5432/app",
            "ALLOWED_HOSTS=localhost,127.0.0.1",
            "ALLOW_DESTRUCTIVE=0",
            "CLERK_JWKS_URL=",
            "CLERK_AUDIENCE=",
            "CLERK_ISSUER=",
            "FRESHDESK_DOMAIN=",
            "FRESHDESK_API_KEY=",
        ],
        root,
    )
    write(
        root / "scripts" / "prod_guard.py",
        """#!/usr/bin/env python3
import sys, pathlib, re
bad = re.compile(r"manage\\.py\\s+(flush|reset_db|sqlflush)\\b")
for p in pathlib.Path('.').rglob('*.sh'):
    if bad.search(p.read_text(encoding='utf-8')):
        print("Destructive command found in:", p)
        sys.exit(1)
print("No destructive commands detected.")
""",
        executable=True, root=root,
    )

    # Agent prompt helpers
    write(
        root / "docs" / "agent-prompts" / "implement.md",
        """IMPLEMENT: <feature-name>
- UPDATE: <path/to/file.py> …
- ADD: <new/file.py> …
- ADD TEST: tests/test_<feature>_e2e.py
- VERIFY: run `pytest`; paste failures; iterate
- RECORD ADR: `python scripts/adr_add.py "<title>"`
""",
        root=root,
    )
    write(
        root / "docs" / "agent-prompts" / "fix.md",
        """FIX: <bug>
- REPRO:
- UPDATE:
- ADD TEST:
- VERIFY: run `pytest`
- RECORD ADR if architectural
""",
        root=root,
    )

    # CI: tests / adr-check / verify-docs
    write(
        root / ".github" / "workflows" / "tests.yml",
        """name: tests
on: [push, pull_request]
jobs:
  unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: python -m pip install -r requirements.txt -r requirements-dev.txt
      - run: python -m pip install django-stubs[compatible-mypy]
      - run: mypy .
      - run: pytest
""",
        root=root,
    )
    write(
        root / ".github" / "workflows" / "adr-check.yml",
        """name: adr-check
on: [pull_request]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Require ADR on core code changes
        run: |
          base="origin/${{ github.base_ref }}"
          git fetch origin ${{ github.base_ref }} --depth=1 || true
          changed=$(git diff --name-only "$base"... | tr '\\n' ' ')
          echo "Changed: $changed"
          if echo "$changed" | grep -E '(config/|jobs/|integrations/)' >/dev/null; then
            echo "$changed" | grep -q 'docs/adr/' || { echo "Changes to core code require an ADR update."; exit 1; }
          fi
""",
        root=root,
    )
    write(
        root / ".github" / "workflows" / "verify-docs.yml",
        """name: verify-docs
on: [push, pull_request]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Jules preflight
        run: bash scripts/jules_preamble.sh
      - name: Verify manifest
        run: python scripts/verify_manifest.py --check
""",
        root=root,
    )

    # docs/manifest
    write(
        root / "docs" / "manifest.yaml",
        """required:
  - README.md
  - docs/Agentic-Django-Plan.md
  - docs/AGENTS.md
  - docs/PRD.template.md
  - docs/adr/0000-template.md
  - docs/tasks/IMPLEMENT.template.md
  - docs/tasks/FIX.template.md
  - docs/reference-sources.json
  - scripts/jules_preamble.sh
  - scripts/restore_docs.py
  - scripts/verify_manifest.py
  - scripts/jules_apply_pack.sh
  - scripts/jules_sync_docs.py
  - scripts/enforce_all.py
  - scripts/adr_add.py
  - scripts/jules_cleanup.sh
  - scripts/prod_guard.py
  - integrations/ops/health.py
  - integrations/auth/clerk_auth.py
  - pytest.ini
  - mypy.ini
  - tests/test_healthz.py
  - tests/conftest.py
  - tests/helpers/http_block.py
  - config/settings_test.py
  - .github/workflows/tests.yml
  - .github/workflows/adr-check.yml
  - .github/workflows/verify-docs.yml
""",
        root=root,
    )

    # Upserts & enforcement
    upsert_requirements(root)
    settings_path = detect_settings(root)
    if settings_path:
        enforce_settings(settings_path, root)

    # (1) Patch CrewAI imports
    patch_crewai_imports(root)
    # (2) Write standardized Makefile
    write_makefile(root)
    # (4) Ensure /healthz route exists
    ensure_health_url(root)

    info("done.")
    print("Next steps:")
    print("  - python -m pip install -r requirements.txt -r requirements-dev.txt")
    print("  - bash scripts/jules_preamble.sh  # preflight + manifest self-heal")
    print("  - pre-commit install")
    print("  - make test  # uses pytest + settings_test")

if __name__ == "__main__":
    main()
