# Based on <https://github.com/astral-sh/uv-docker-example/blob/main/Dockerfile>

FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Enable bytecode compilation - trade longer installation for faster start-up times.
ENV UV_COMPILE_BYTECODE=1

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

ADD . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev
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

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "testdjereo.wsgi:application"]
