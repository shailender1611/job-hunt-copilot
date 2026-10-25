.PHONY: install lint format typecheck test check

install:
	uv sync

lint:
	uv run ruff check src tests

format:
	uv run ruff format src tests

typecheck:
	uv run mypy src

test:
	uv run pytest --cov=copilot

check: lint typecheck test
