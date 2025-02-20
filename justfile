# testdjereo - local development tooling

set dotenv-load
set positional-arguments

default:
  @just --list

_dev_setup:
  @test -d .venv/ || uv venv
  @test -x .venv/bin/django-admin || uv sync --dev
  @uv pip install -e .

manage +args='help': _dev_setup
  @uv run manage.py "$@"

runserver $PYTHONDEVMODE="1": _dev_setup
  # Disable PYTHONDEVMODE by passing an empty string ie. `just runserver ""`
  @if ! $DEBUG; then \
    rm -rf static/; \
    uv run manage.py collectstatic --noinput; \
  fi
  @uv run manage.py runserver

shell: _dev_setup
  @uv run manage.py shell

test +args='.':
  @test -d .venv/ || uv venv
  @test -x .venv/bin/coverage || uv sync --group test
  @uv pip install -e .
  @uv run coverage erase
  @uv run python -m coverage run --source="." manage.py test "$@" --verbosity=3 --failfast --pdb
  @uv run coverage report
  @uv run coverage html
