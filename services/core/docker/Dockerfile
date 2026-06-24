FROM ghcr.io/astral-sh/uv:python3.10-alpine AS builder

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=0 \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app

RUN apk add --no-cache gcc musl-dev postgresql-dev

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv sync --frozen --no-dev

FROM python:3.10-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

RUN addgroup -S django && adduser -S -G django django

RUN apk add --no-cache libpq && pip install --no-cache-dir uv

COPY --from=builder /opt/venv /opt/venv
RUN chown -R django:django /opt/venv

WORKDIR /app

COPY --from=builder /app /app

RUN chmod +x docker/entrypoint.sh && chown -R django:django /app

USER django

EXPOSE 8000

CMD ["/bin/sh", "docker/entrypoint.sh"]
