
# testdjereo - local development tooling

set positional-arguments

call_recipe := just_executable() + " --justfile=" + justfile()

default_addrport := '127.0.0.1:8000'

default:
  @just --list

collectstatic:
  #!/usr/bin/env bash
  # It would be simpler to use just's `dotenv-load`. However, this is not a viable
  # approach since this would also load `.env` for the `test` recipe. Meaning the
  # environment `test` runs in would be polluted instead of using values from `.env.test`.
  set -euo pipefail
  DEBUG_VALUE="false"
  if [ -f .env ]; then
    # Extract DEBUG from .env (strip whitespace, lowercase). Default to "false" if missing.
    DEBUG_VALUE=$(awk -F= '/^DEBUG=/{gsub(/["'\'' ]/, "", $2); print tolower($2)}' .env || echo "false")
  fi
  if [ "$DEBUG_VALUE" = "false" ]; then
    rm -rf static/;
    uv run manage.py collectstatic --noinput;
  fi

_dev_setup:
  @test -d .venv/ || uv venv
  @test -x .venv/bin/django-admin || uv sync --dev
  @uv pip install -e .
  {{call_recipe}} collectstatic

manage +args='help': _dev_setup
  @uv run manage.py "$@"

runserver addrport=default_addrport $PYTHONDEVMODE="1": _dev_setup
  # Disable PYTHONDEVMODE by passing an empty string ie. `just runserver 127.0.0.1:8000 ""`
  MP_DATABASE=mailpit.db mailpit &
  @uv run manage.py runserver {{addrport}}

shell: _dev_setup
  @uv run manage.py shell

_test_setup:
  @test -d .venv/ || uv venv
  @test -x .venv/bin/coverage || uv sync --group test
  @uv pip install -e .

profile_tests: _test_setup
  @sudo py-spy record --subprocesses --format speedscope -o profile.speedscope.json -- \
    uv run python manage.py test

e2e $USE_ENV_TEST="1": _test_setup
  #!/usr/bin/env bash
  set -euo pipefail
  #mailpit &
  #MAILPIT_PID=$!
  uv run manage.py flush --no-input
  uv run manage.py migrate
  uv run manage.py seed_database
  uv run manage.py runserver "" &
  SERVER_PID=$!
  uv run pytest tests_e2e/ --pdb || STATUS=$?
  kill $SERVER_PID
  #kill $MAILPIT_PID
  exit ${STATUS:-0}
