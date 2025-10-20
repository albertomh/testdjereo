from enum import Enum

from testdjereo_deploy._types import (
    Environment,
)
from testdjereo_deploy.infra._types import EnvironmentBlueprint


class WELL_KNOWN_UUIDS(Enum):
    pass


BLUEPRINT = EnvironmentBlueprint(
    #
    environment=Environment.LIVE,
    #
    droplets=[],
)
