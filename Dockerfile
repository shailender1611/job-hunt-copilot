# ---------- build: resolve and install locked dependencies ----------
FROM python:3.12-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app

# Dependencies first so this layer is cached across code changes.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-install-project

COPY src ./src
RUN uv sync --locked --no-dev

# ---------- runtime: slim image, non-root user ----------
FROM python:3.12-slim
RUN useradd --create-home app
WORKDIR /app
COPY --from=build --chown=app /app /app
COPY --chown=app ui ./ui
COPY --chown=app .streamlit ./.streamlit
USER app

ENV PATH="/app/.venv/bin:$PATH" PORT=8501
EXPOSE 8501
HEALTHCHECK CMD python -c "import urllib.request,os; urllib.request.urlopen(f'http://localhost:{os.environ[\"PORT\"]}/_stcore/health')"

# PORT is injected by Render / HF Spaces (7860); defaults to 8501 locally.
CMD streamlit run ui/streamlit_app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
