FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./
COPY scripts ./scripts

USER root

ENV UV_PROJECT_ENVIRONMENT="/app/.venv"

RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

RUN chmod +x scripts/db_entrypoint.sh

CMD ["sh", "-c", "uvicorn acme_ops_agent.api.app:app --host ${API_HOST:-0.0.0.0} --port ${API_PORT:-8000}"]