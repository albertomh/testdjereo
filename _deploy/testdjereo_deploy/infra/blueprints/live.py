from enum import Enum

from testdjereo_deploy._types import (
    Environment,
    EnvironmentBlueprint,
)


class WELL_KNOWN_UUIDS(Enum):
    pass


BLUEPRINT = EnvironmentBlueprint(
    #
    environment=Environment.LIVE,
    #
    droplets=[],
)
