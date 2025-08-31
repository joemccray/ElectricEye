# jules-backend-testsuite-prompts.md (Portable)

**Goal:** A stable, repeatable **Django + pytest** backend test environment that:
- avoids `ImportError: attempted relative import with no known parent package`,
- blocks outbound network by default,
- uses SQLite in-memory for speed,
- stubs AWS with `botocore.stub.Stubber` / `moto`,
- **works on any Django project** (no hard-coded app names).

**Assumptions**
- Python ≥ 3.11 is available.
- Repo root is the working directory.
- Tests live under `tests/`, `**/tests/`, and optionally `scans/` (edit as needed).
- If your settings module can’t be auto-detected, set `DJANGO_SETTINGS_MODULE` before running prompts.

> **Golden rules for every prompt**
> 1) Run from repo root. 2) Keep steps atomic: *write → add → commit*.  
> 3) No network: install from requirements; mock external calls.  
> 4) Make all packages importable via `__init__.py` + `pytest.ini[pythonpath=. ]` + editable install.

---

## Prompt 0 — Preflight & branch
```bash
set -euxo pipefail
git fetch --all --prune || true
DEFAULT_BRANCH="$(git remote show origin 2>/dev/null | sed -n '/HEAD branch/s/.*: //p' || true)"; DEFAULT_BRANCH="${DEFAULT_BRANCH:-main}"
git checkout -B feat/backend-tests "origin/${DEFAULT_BRANCH}" || git checkout -B feat/backend-tests || git checkout feat/backend-tests

python -V
python -c "import sys; assert sys.version_info[:2] >= (3,10), 'Python >=3.10 required'"
```

---

## Prompt 1 — Pin Python + create venv (.venv) and upgrade pip
```bash
set -euxo pipefail
echo "3.11" > .python-version
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip wheel setuptools
git add .python-version && git commit -m "chore(py): pin python to 3.11" || true
```

---

## Prompt 2 — Requirements (dev/test) and install **offline-friendly**
```bash
set -euxo pipefail
. .venv/bin/activate

mkdir -p requirements
[ -f requirements/dev.txt ] || cat > requirements/dev.txt <<'EOF'
pytest>=8
pytest-cov>=5
pytest-django>=4
pytest-xdist>=3
pytest-socket>=0.6
moto[boto3]>=5
boto3>=1.34
botocore>=1.34
freezegun>=1.4
faker>=25
EOF

# Main requirements only if none exist
if ! [ -f requirements.txt ] && ! [ -f pyproject.toml ] && ! [ -f setup.cfg ] && ! [ -f setup.py ]; then
  cat > requirements.txt <<'EOF'
Django>=4.2,<5.0
EOF
fi

python -m pip install -r requirements/dev.txt || true
[ -f requirements.txt ] && python -m pip install -r requirements.txt || true
```

---

## Prompt 3 — **Portable** package discoverability (add `__init__.py`)
> Ensures every top-level package is a real package so imports work.
```bash
set -euxo pipefail
for d in */ ; do
  case "$d" in .*|.git/|node_modules/|.venv/|venv/|dist/|build/|static/|media/|docs/|scripts/|migrations/|tests/|e2e/ ) continue ;; esac
  [ -d "$d" ] || continue
  if find "$d" -maxdepth 2 -type f -name "*.py" | grep -q . ; then
    [ -f "${d%/}/__init__.py" ] || : > "${d%/}/__init__.py"
  fi
done
git add -A && git commit -m "test(pkg): add __init__.py to package roots for importability" || true
```

---

## Prompt 4 — **Portable** pyproject for editable install (find packages)
```bash
set -euxo pipefail
if [ ! -f pyproject.toml ] && [ ! -f setup.cfg ] && [ ! -f setup.py ]; then
  cat > pyproject.toml <<'EOF'
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "local-backend"
version = "0.0.0"
description = "Local backend (auto-discovered packages)"
requires-python = ">=3.10"

[tool.setuptools]
include-package-data = true

[tool.setuptools.packages.find]
where = ["."]
include = ["*"]
exclude = ["tests*", "*tests*", "e2e*", "docs*", "scripts*", "node_modules*", "dist*", "build*"]
EOF
  git add pyproject.toml && git commit -m "build: portable pyproject with setuptools.find_packages" || true
fi

. .venv/bin/activate
python -m pip install -e . || true
```

---

## Prompt 5 — **Portable** pytest config (auto-detect settings; overridable)
```bash
set -euxo pipefail

# Allow manual override via env
if [ -n "${DJANGO_SETTINGS_MODULE:-}" ]; then
  DETECTED_SETTINGS="$DJANGO_SETTINGS_MODULE"
else
  DETECTED_SETTINGS="$(python - <<'PY'
import os
candidates=[]
for root, dirs, files in os.walk('.'):
    if 'settings.py' in files:
        skip = any(seg in {'.venv','venv','node_modules','.git','dist','build','migrations'} for seg in root.split(os.sep))
        if skip: continue
        mod = os.path.relpath(os.path.join(root, 'settings.py'), '.').replace(os.sep, '.')[:-3]
        candidates.append(mod)
print(candidates[0] if candidates else 'project.settings')
PY
)"
fi

cat > pytest.ini <<EOF
[pytest]
addopts = -q -ra --maxfail=1 --disable-warnings
testpaths = tests **/tests scans
pythonpath = .
DJANGO_SETTINGS_MODULE = ${DETECTED_SETTINGS}
markers =
    django_db: marks tests as using the Django DB
    aws: marks tests that stub AWS calls
EOF

git add pytest.ini && git commit -m "test(cfg): portable pytest.ini (pythonpath=., DJANGO_SETTINGS_MODULE=${DETECTED_SETTINGS})" || true
```

---

## Prompt 6 — Test settings module: fast SQLite, locmem services
```bash
set -euxo pipefail
mkdir -p config
cat > config/settings_test.py <<'EOF'
from importlib import import_module
import os

BASE_MODULE = os.environ.get("BASE_DJANGO_SETTINGS", "")
if BASE_MODULE:
    globals().update(import_module(BASE_MODULE).__dict__)

SECRET_KEY = "test-secret-key"
DEBUG = True
ALLOWED_HOSTS = ["*"]

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
EOF

# Point pytest to test settings (overrides the auto-detected one)
sed -i.bak -E 's#^(DJANGO_SETTINGS_MODULE\s*=\s*).+#\1config.settings_test#' pytest.ini || true
git add config/settings_test.py pytest.ini && git commit -m "test(cfg): sqlite in-memory + locmem; use config.settings_test" || true
```

---

## Prompt 7 — Root `conftest.py`: sys.path, block network, AWS env
```bash
set -euxo pipefail
cat > conftest.py <<'EOF'
import os, sys, pathlib, pytest
# Ensure repo root on sys.path
ROOT = pathlib.Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Block network by default (pytest-socket if available)
try:
    import pytest_socket  # type: ignore
    pytest_plugins = ("pytest_socket",)
    def pytest_runtest_setup(item):
        from pytest_socket import disable_socket
        disable_socket()
except Exception:
    pass

# AWS safety
os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")
os.environ.setdefault("BOTO_CONFIG", "/dev/null")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

@pytest.fixture
def enable_network():
    """Opt-in network access when a test truly needs it."""
    from pytest_socket import enable_socket
    enable_socket()
EOF
git add conftest.py && git commit -m "test(cfg): conftest adds root to sys.path, blocks network, sets AWS env" || true
```

---

## Prompt 8 — AWS stubbing helper (generic)
```bash
set -euxo pipefail
mkdir -p tests/utils
cat > tests/utils/aws.py <<'EOF'
from contextlib import contextmanager
from botocore.stub import Stubber
import boto3

@contextmanager
def stubbed_client(service, **kwargs):
    client = boto3.client(service, **kwargs)
    with Stubber(client) as stub:
        yield client, stub

# Example:
# with stubbed_client("s3") as (s3, stub):
#     stub.add_response("list_buckets", {"Buckets": []})
#     assert s3.list_buckets()["Buckets"] == []
EOF
git add tests/utils/aws.py && git commit -m "test(util): AWS stubbed_client helper" || true
```

---

## Prompt 9 — Django bootstrap smoke (only if Django installed)
```bash
set -euxo pipefail
. .venv/bin/activate
python - <<'PY'
try:
    import django  # noqa: F401
except Exception:
    print("Django not installed; skipping bootstrap")
    raise SystemExit(0)

import os, django as dj
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings_test")
dj.setup()
print("Django setup OK")
PY
```

---

## Prompt 10 — Collection smoke (catches import/path errors fast)
```bash
set -euxo pipefail
. .venv/bin/activate
pytest -q --collect-only
```

---

## Prompt 11 — Fast run (no e2e), validate AWS mocking & DB
```bash
set -euxo pipefail
. .venv/bin/activate
pytest -q -k "not e2e" --maxfail=1 --disable-warnings
```

---

## Prompt 12 — Coverage config + run
```bash
set -euxo pipefail
cat > .coveragerc <<'EOF'
[run]
omit =
    */migrations/*
    */tests/*
    */__init__.py
    */settings*.py

[report]
skip_empty = True
show_missing = True
EOF
git add .coveragerc && git commit -m "test(cov): add coverage config" || true

. .venv/bin/activate
pytest --cov=. --cov-report=term-missing:skip-covered
```

---

## Prompt 13 — **Optional/Opt-in** import rewrite (only if needed)
```bash
set -euxo pipefail
# Set MAIN_PKG to rewrite fragile relative imports inside that package only.
# Example: MAIN_PKG=myproj bash -lc '...'
if [ -n "${MAIN_PKG:-}" ] && [ -d "$MAIN_PKG" ]; then
  find "$MAIN_PKG" -type f -name "*.py" -print0 | xargs -0 sed -E -i.bak "s/^from \.(\w+)/from ${MAIN_PKG}.\1/g" || true
  git add -A && git commit -m "fix(imports): rewrite relative imports in ${MAIN_PKG} to absolute" || true
else
  echo "Skipping import rewrites; set MAIN_PKG to opt in."
fi
```

---

## Prompt 14 — Re-run smoke & targeted tests
```bash
set -euxo pipefail
. .venv/bin/activate
pytest -q --collect-only
pytest -q -k "aws or django_db" --maxfail=1
```

---

## Prompt 15 — Makefile shortcuts (optional)
```bash
set -euxo pipefail
cat > Makefile <<'EOF'
.PHONY: venv deps test cov
venv: .venv/bin/activate
.venv/bin/activate:
	python -m venv .venv && . .venv/bin/activate && python -m pip install --upgrade pip

deps:
	. .venv/bin/activate && python -m pip install -r requirements/dev.txt \
	&& { [ -f requirements.txt ] && python -m pip install -r requirements.txt || true; } \
	&& python -m pip install -e .

test:
	. .venv/bin/activate && pytest -q

cov:
	. .venv/bin/activate && pytest --cov=. --cov-report=term-missing:skip-covered
EOF
git add Makefile && git commit -m "chore: add Makefile (venv, deps, test, cov)" || true
```

---

## Prompt 16 — CI workflow (GitHub Actions)
```bash
set -euxo pipefail
mkdir -p .github/workflows
cat > .github/workflows/backend-ci.yml <<'EOF'
name: backend-ci
on: [push, pull_request]
jobs:
  tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: python -m venv .venv && . .venv/bin/activate && python -m pip install --upgrade pip
      - run: . .venv/bin/activate && python -m pip install -r requirements/dev.txt
      - run: . .venv/bin/activate && [ -f requirements.txt ] && python -m pip install -r requirements.txt || true
      - run: . .venv/bin/activate && python -m pip install -e . || true
      - run: . .venv/bin/activate && pytest --maxfail=1 --disable-warnings -q
EOF
git add .github/workflows/backend-ci.yml && git commit -m "ci: add portable backend pytest workflow" || true
```

---

## Prompt 17 — Enforce no network in CI (sanity)
```bash
set -euxo pipefail
. .venv/bin/activate
python - <<'PY'
import importlib.util, sys
ok = bool(importlib.util.find_spec("pytest_socket"))
print("pytest-socket present:", ok)
sys.exit(0 if ok else 1)
PY
```

---

## Prompt 18 — Final full run with coverage
```bash
set -euxo pipefail
. .venv/bin/activate
pytest --cov=. --cov-report=xml --cov-report=term-missing:skip-covered
```

---

## Prompt 19 — Push branch & PR (if remote available)
```bash
set -euxo pipefail
git push -u origin feat/backend-tests || true
echo "Open PR: test(backend): portable pytest + sqlite test settings + AWS stubs + CI"
```

---

## Prompt 20 — README quick start (portable)
```bash
set -euxo pipefail
awk 'BEGIN{p=1}/<!-- BACKEND-TESTS-INJECT-START -->/{p=0}1' README.md 2>/dev/null > README.md.tmp || true
cat > README.md.add <<'EOF'
<!-- BACKEND-TESTS-INJECT-START -->
## Backend tests: quick start (portable)

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements/dev.txt
[ -f requirements.txt ] && python -m pip install -r requirements.txt
python -m pip install -e .
pytest -q
```

- Config: `pytest.ini` sets `pythonpath = .`. `DJANGO_SETTINGS_MODULE` is auto-detected, then overridden to `config/settings_test.py` for speed.
- Imports: `__init__.py` + editable install make packages importable without hard-coded names.
- Network: disabled by default (pytest-socket); opt-in with the `enable_network` fixture.
- AWS: stub with `tests/utils/aws.py` helper or `moto`.
<!-- BACKEND-TESTS-INJECT-END -->
EOF
{ cat README.md.add; echo; cat README.md 2>/dev/null; } > README.md
rm -f README.md.add README.md.tmp || true
git add README.md && git commit -m "docs(test): backend tests quick-start (portable)" || true
```

---

**Result**
- No hard-coded app names; packages discovered generically.
- Import/path issues avoided by `__init__.py`, `pythonpath = .`, and `pip install -e .`.
- Django test settings give deterministic, fast tests.
- AWS + network access are safe by default.
- CI reproduces local behavior to prevent regressions.
