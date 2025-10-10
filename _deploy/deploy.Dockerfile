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

FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PORT=

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# - Silence uv complaining about not being able to use hard links.
# - Enable bytecode compilation - trade longer installation for faster start-up times.
# - Prevent uv from accidentally downloading isolated Python builds.
# - Declare `/app` as the target for `uv sync`.
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# uv sync:
#     --locked: Assert that `uv.lock` will remain unchanged as part of running `uv sync`.

# Synchronise dependencies without the application itself.
# Cached until `uv.lock` or `pyproject.toml` change.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync \
        --locked \
        --no-dev \
        --no-install-project

# Install the application without dependencies.
ADD . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync \
        --locked \
        --no-dev \
        --no-editable
RUN uv pip install .

# Make executables available in the environment.
ENV PATH="/app/.venv/bin:$PATH"

# Invoke with `docker build` with `--build-arg CACHEBUST=$(date +%s)` to bust layer cache.
ARG CACHEBUST=1

COPY _deploy/.env.deploy .env
RUN python manage.py collectstatic --noinput
RUN rm .env

# Reset the entrypoint, avoid base image's call to `uv`.
ENTRYPOINT []

# `sh -c` allows variable expansion ($PORT) while allowing for the benefits of 'exec form'
# (CMD [...]) over 'shell form' (CMD ...). Benefits include preserving signal handling and
# improved container shutdown behavior.
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT testdjereo.wsgi:application"]
