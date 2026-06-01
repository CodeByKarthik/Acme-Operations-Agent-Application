FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

COPY acme-ops-agent ./acme-ops-agent
COPY acme-ops-mcp/pyproject.toml acme-ops-mcp/uv.lock acme-ops-mcp/README.md ./acme-ops-mcp/
COPY acme-ops-mcp/src ./acme-ops-mcp/src

WORKDIR /app/acme-ops-mcp

RUN uv sync --frozen --no-dev


FROM python:3.13-slim AS runtime

WORKDIR /app/acme-ops-mcp

ENV PATH="/app/acme-ops-mcp/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

COPY --from=builder /app/acme-ops-mcp /app/acme-ops-mcp
COPY --from=builder /app/acme-ops-agent /app/acme-ops-agent

CMD ["python", "-m", "acme_ops_mcp.mcp.server"]