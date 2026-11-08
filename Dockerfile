# Reproducible runtime image. Pattern credit: multi-stage uv build from agent-service-toolkit (docker/).
FROM python:3.12-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev

FROM python:3.12-slim
RUN useradd --create-home --uid 10001 iat
WORKDIR /app
COPY --from=build /app /app
ENV PATH="/app/.venv/bin:$PATH" IAT_HOST=0.0.0.0 IAT_PORT=8000
USER iat
EXPOSE 8000
# IAT_JWT_SECRET must be supplied at runtime (e.g. --env-file .env); the service refuses to start without it.
CMD ["iat-serve"]
