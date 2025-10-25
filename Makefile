PY := $(shell command -v python)
VENV := .venv.buildtest
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest

.PHONY: build clean test

build: clean-dist venv.test test

venv.test:
	rm -rf $(VENV)
	$(PY) -m venv $(VENV)
	$(PIP) install pytest pytest-cov pytest-asyncio
	$(PIP) install $(shell ls -1t dist/live_template-*.whl 2>/dev/null | head -n1)"[aiogram]"
	$(PYTEST) -q --cov --cov-report=term-missing

clean-dist:
	rm -rf dist/*
	poetry build

test:
	#poetry run pytest -q --cov --cov-report=term-missing
	poetry run pytest -q

clean:
	rm -rf dist $(VENV)

