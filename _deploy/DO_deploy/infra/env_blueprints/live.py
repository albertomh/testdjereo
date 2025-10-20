from enum import Enum

from DO_deploy._types import (
    Environment,
)
from DO_deploy.infra._types import EnvironmentBlueprint


class WELL_KNOWN_UUIDS(Enum):
    pass


BLUEPRINT = EnvironmentBlueprint(
    #
    environment=Environment.LIVE,
    #
    droplets=[],
)
