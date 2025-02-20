# testdjereo developer README

## Git principles

This repo follows trunk-based development. This means:

- the `main` branch should always be in a releasable state
- use short-lived feature branches

Please follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)
guidelines when writing commit messages. `commitlint` is enabled as a pre-commit hook.
Valid commit types are defined in `.commitlintrc.ts`.

## Justfile recipes

Four recipes are ready to use in every new project. Each takes care of setting up a
virtual environment and installing dependencies (including the project itself in editable
mode).

- `manage`: wrapper around Django's `manage.py`. Takes one or more arguments, which
  defaults to 'help'.
- `runserver`: execute Django's `runserver` management command using Python in
  [Development Mode](https://docs.python.org/3/library/devmode.html).
  This mode shows additional warnings (Deprecation, Import, Resource) and enables extra
  debug hooks. Development Mode can be disabled by passing an empty string
  i.e. `just runserver ""`
- `shell`: run Django's management command to drop into a shell. By default this is IPython
  in all new projects.
- `test`: install test dependencies, run all unit tests via Django's test runner and
  generate and display a coverage report (both on-screen and in HTML format).

### Use project metadata in the running application

`testdjereo/__init__.py` exposes project metadata such as version and author information.
To use it in a view:

```python
from django.http import HttpResponse

from testdjereo import __version__


def view(request):
    return HttpResponse(f"testdjereo v{__version__}")
```

### Use IPython as your shell

`IPython`, an improved Python shell, is installed as a development dependency. Django picks
it up by default and uses it instead of the default Python shell.
To use `IPython` run `manage.py shell` or the `just shell` recipe.

By default IPython's debugger (`ipdb`) will launch when a `breakpoint()` is reached while
running the application.
`ipdb` is also used to debug tests and will launch when a test fails.

## Developer tools

The project comes with some ready-to-use developer tools installed as dev dependencies and
configured for use locally:

- [django-browser-reload](https://pypi.org/project/django-browser-reload/): reload the browser
  when project files change.
- [django-debug-toolbar](https://pypi.org/project/django-debug-toolbar/): display information
  about the request/response cycle on each page.
- [rich](https://pypi.org/project/rich/): nicer formatting and colours for `runserver` logs.

## Checks and git hooks

`ruff` is configured as a pre-commit git hook to lint and format your code. Check the
`tool.ruff.lint` table in `pyproject.toml` for a full list of rules and options.
Notable rules include:

- [banned-api](https://docs.astral.sh/ruff/rules/banned-api/) from the `flake8-tidy-imports`
linter. Configured to ban importing the project settings module directly, preferring to use
`django.conf.settings`. This is to improve consistency, particulary when overriding
settings in tests.

## Upgrade checklist

- [ ] Bump the version of Django specified in the config for the `django-upgrade` hook in
      `.pre-commit-config.yaml`.

## GitHub Actions

### Custom GitHub actions

Three re-usable custom actions are available:

- `pre-commit`: runs all pre-commit hooks except `no-commit-to-branch` as this would
   make merge pipelines fail. In workflows (see below) all jobs depend on this action
   succeeding.
- `sys-check`: runs Django's system checks (`manage.py check`).
- `test`: runs all unit tests via the `just test` recipe (see [Justfile recipes](#justfile-recipes)).

See [.github/actions/](https://github.com/albertomh/djereo/tree/main/template/%7B%25if%20is_github_project%25%7D.github%7B%25endif%25%7D/actions)
for the definitions of these actions.

### GitHub Actions workflows

Four workflows are defined:

#### `PR` (pull request)

Runs whenever a pull request is opened against a branch or an existing PR receives new commits.

#### `CI` (continuous integration)

As with `PR`, but acts when a pull request is closed and changes merged into the `main` branch.

#### Release Please

Refreshes a pull request that updates the changelog & bumps the Semantic Version every
time the `main` branch is merged to.
[.release-please-config.json](https://github.com/albertomh/djereo/blob/main/template/%7B%25if%20is_github_project%25%7D.release-please-config.json%7B%25endif%25%7D.jinja)
configures the tool while [.release-please-manifest.json](https://github.com/albertomh/djereo/blob/main/template/%7B%25if%20is_github_project%25%7D.release-please-manifest.json%7B%25endif%25%7D.jinja)
is the source of truth for the latest SemVer tag.

**N.B.** conventional commits (as enforced by the relevant git hook) are a prerequisite
for Release Please to generate changelogs and calculate new SemVer tags.

In order for Release Please to automate the above process, a GitHub Actions 'repository secret'
called `RELEASE_PLEASE_TOKEN` must exist in GitHub (under `github.com/<user>/<repo>/secrets/actions`).
The contents of this secret must be a Personal Access Token (PAT) with the following permissions:

```yaml
contents: write
pull-requests: write
```

For more information, consult the [release-please-action project](https://github.com/googleapis/release-please-action).

#### Dependabot

Configured to update Python dependencies & GitHub actions on a weekly schedule.

See [.github/workflows/](https://github.com/albertomh/djereo/tree/main/template/%7B%25if%20is_github_project%25%7D.github%7B%25endif%25%7D/workflows)
and [.github/dependabot.yaml](https://github.com/albertomh/djereo/blob/main/template/%7B%25if%20is_github_project%25%7D.github%7B%25endif%25%7D/dependabot.yaml)
for the definitions of these workflows.

## Upgrading

Project `settings` will look for a list of `SECRET_KEY_FALLBACKS` in the `.env` file that
can be used to rotate keys. This defaults to an empty list.

---

&copy; Alberto Morón Hernández
