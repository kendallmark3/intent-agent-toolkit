# Runtime image. Pattern credit: multi-stage uv build from agent-service-toolkit (docker/).
# INTENT-003: pinned uv that reads lockfile revision 3; app installed as a built package (not an
# editable source tree); non-root; health check; smoke-tested in CI (.github/workflows/ci.yml).
FROM python:3.12-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable

FROM python:3.12-slim
RUN useradd --create-home --uid 10001 iat
WORKDIR /app
COPY --from=build /app/.venv /app/.venv
# API docs are off by default in the image (independent finding C-033); set IAT_DOCS_ENABLED=true to opt in.
ENV PATH="/app/.venv/bin:$PATH" IAT_HOST=0.0.0.0 IAT_PORT=8000 IAT_DOCS_ENABLED=false PYTHONDONTWRITEBYTECODE=1
USER iat
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health/ready', timeout=3).status == 200 else 1)"]
# IAT_JWT_SECRET must be supplied at runtime (e.g. --env-file .env); the service refuses to start without it.
CMD ["iat-serve"]
