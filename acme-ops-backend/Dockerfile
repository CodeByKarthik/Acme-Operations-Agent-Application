FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

# Copy shared dependency (acme-ops-shared)
COPY acme-ops-shared ./acme-ops-shared

# Copy backend package
COPY acme-ops-backend/pyproject.toml acme-ops-backend/uv.lock acme-ops-backend/README.md ./acme-ops-backend/
COPY acme-ops-backend/src ./acme-ops-backend/src

WORKDIR /app/acme-ops-backend

USER root

ENV UV_PROJECT_ENVIRONMENT="/app/acme-ops-backend/.venv"

RUN uv sync --frozen --no-dev

ENV PATH="/app/acme-ops-backend/.venv/bin:$PATH"
ENV PYTHONPATH="/app/acme-ops-backend/src"

CMD ["sh", "-c", "uvicorn acme_ops_backend.api.app:app --host ${API_HOST:-0.0.0.0} --port ${API_PORT:-8000}"]