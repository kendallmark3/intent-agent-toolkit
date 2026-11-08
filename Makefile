.PHONY: install run test lint typecheck security intent check demo

install:
	uv sync

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
