# Usage:
#
# ```
# docker network create testdjereo_net
# docker image pull --platform linux/amd64 <registry>/<image>:<tag>
#
# docker run --detach --name testdjereo \
#     --user root \
#     --env-file /etc/testdjereo/.env \
#     --env PORT=8000 \
#     --network testdjereo_net \
#     --publish 8000:8000 \
#     --volume testdjereo_static:/app/static \
#     <registry>/<image>:<tag>
# ```
#
# Based on <https://github.com/astral-sh/uv-docker-example/blob/main/Dockerfile>

FROM python:3.14-slim-bookworm AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# - Silence uv complaining about not being able to use hard links.
# - Enable bytecode compilation - trade longer installation for faster start-up times.
# - Prevent uv from accidentally downloading isolated Python builds.
# - Declare `/app` as the target for `uv sync`.
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install build dependencies
# Only needed while `brotli` wheels for 3.14 aren't available
# <https://github.com/google/brotli/issues/1351>
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*
# TODO: remove sqlite3 from list - just for dev!

# Synchronise dependencies (creates .venv)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync \
        --frozen \
        --no-dev

COPY . .
COPY _deploy/.env.deploy .env
# Install the webapp (dependencies already installed by `uv sync`)
RUN uv pip install . --no-deps

RUN python manage.py collectstatic --noinput && rm .env

# ----------------------------------------------------------------------------------------
# runtime stage

# TODO: read <https://www.joshkasuboski.com/posts/distroless-python-uv/>

FROM python:3.14-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

# TODO: remove sqlite3 installation step - just for dev!
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app /app

ENTRYPOINT []

# `sh -c` allows variable expansion ($PORT) while allowing for the benefits of 'exec form'
# (CMD [...]) over 'shell form' (CMD ...). Benefits include preserving signal handling and
# improved container shutdown behavior.
CMD ["sh", "-c", "python -m gunicorn --bind 0.0.0.0:${PORT} testdjereo.wsgi:application"]
