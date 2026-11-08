.PHONY: install setup env token run test lint typecheck security intent check demo smoke console-check

install:
	uv sync

# First run: install dependencies and create .env with a generated secret (never overwrites).
setup: install env

env:
	uv run python scripts/init_env.py

# Print a local bearer token for the console or curl (signed with IAT_JWT_SECRET from .env).
token:
	@uv run iat-token --sub $${IAT_SUB:-$${USER:-developer}}

run:
	uv run iat-serve

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .

typecheck:
	uv run mypy

security:
	uv run bandit -q -c pyproject.toml -r src
	uv export --no-dev --no-hashes --format requirements-txt -o .audit-requirements.txt -q
	uv run pip-audit -r .audit-requirements.txt --progress-spinner off; status=$$?; rm -f .audit-requirements.txt; exit $$status

intent:
	bash hooks/pre-implement.sh
	bash tests/pre-implement.test.sh

check: lint typecheck security test intent

demo:
	uv run python examples/supplier_readiness/demo.py

# Smoke-test a running service (default: local). Example: make smoke BASE_URL=https://...
BASE_URL ?= http://127.0.0.1:8000
smoke:
	uv run python scripts/smoke.py --base-url $(BASE_URL) --token "$$(uv run iat-token --sub smoke)"

# Drive the console in a real browser (needs: pip install playwright && playwright install chromium).
console-check:
	python scripts/console_check.py --base-url $(BASE_URL) --token "$$(uv run iat-token --sub console-check)" --out console-evidence
