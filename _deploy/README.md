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
cp infra/env_blueprints/_sample.py.txt infra/env_blueprints/test.py
# edit the contents of the test.py blueprint ...

uv venv
uv pip install -e .
export DIGITALOCEAN__TOKEN=dop_v1_123...
uv run python -m DO_deploy.infra.apply test [--no-dry-run]

# upload the deployment module to the newly created Droplet(s)
uv run python -m DO_deploy.upload_deployment_script test admin
# deploy the webapp following the blue/green strategy
ssh admin@$dropletIP -t 'cd /etc/testdjereo/; uv run python -m DO_deploy.deploy.blue_green_deploy -u albertomh -t $GH_PAT -i albertomh/testdjereo:latest -n testdjereo'
```
