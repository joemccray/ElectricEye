# Standardized test runner for CI and local
PYTEST ?= pytest -q
export DJANGO_SETTINGS_MODULE ?= config.settings_test

.PHONY: test unit lint typecheck
test: unit
unit:
	$(PYTEST)

lint:
	ruff check .

typecheck:
	mypy .
