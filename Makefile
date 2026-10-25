.PHONY: install lint format typecheck test check run

install:
	uv sync

lint:
	uv run ruff check src tests ui

format:
	uv run ruff format src tests ui

typecheck:
	uv run mypy src ui

test:
	uv run pytest --cov=copilot

check: lint typecheck test

run:
	uv run streamlit run ui/streamlit_app.py
