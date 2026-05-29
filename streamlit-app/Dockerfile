FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src ./src

ENV UV_PROJECT_ENVIRONMENT="/app/.venv"
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"


CMD ["sh", "-c", "streamlit run src/streamlit_app/app.py --server.port=${STREAMLIT_PORT} --server.address=${STREAMLIT_HOST}"]