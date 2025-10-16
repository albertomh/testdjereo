# 🦤 Digital Ocean Deployment Orchestrator

A Python package to

- define infrastructure on Digital Ocean
- create said infrastructure
- manage deploying business logic

## Prerequisites

- [Python 3.14](https://docs.python.org/3.14/) or above
- [uv](https://docs.astral.sh/uv/)

## Quickstart

```sh
# create a blueprint for an environment:
cp infra/blueprints/_sample.py.txt infra/blueprints/test.py
# edit the contents of the test.py blueprint ...

uv venv
uv pip install -e .
export DIGITALOCEAN_TOKEN=dop_v1_123...
uv run python -m testdjereo_deploy.infra.apply test [--no-dry-run]
```
