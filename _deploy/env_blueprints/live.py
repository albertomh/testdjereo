from digitalocean_deployment_orchestrator.infra.types import (
    Environment,
    EnvironmentBlueprint,
)

BLUEPRINT = EnvironmentBlueprint(
    #
    environment=Environment.LIVE,
    #
    droplets=[],
)
