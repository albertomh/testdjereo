from enum import Enum
from uuid import UUID

from testdjereo_deploy._types import (
    DORegion,
    DropletImage,
    DropletRequest,
    DropletSize,
    Environment,
    EnvironmentBlueprint,
)


class WELL_KNOWN_UUIDS(Enum):
    APP_1 = UUID("f57cebc7-3e29-4096-b1a6-c67d84a88019")
    DB_1 = UUID("6bd8663c-9e5d-4890-982f-cc5bffdd6001")


BLUEPRINT = EnvironmentBlueprint(
    #
    environment=Environment.TEST,
    #
    droplets=[
        DropletRequest(
            name="",
            region=DORegion.LONDON1,
            size=DropletSize.BASIC_YOCTO,
            image=DropletImage.DEBIAN_13_X64,
            ssh_keys=[],
            tags=[],
            user_data="",
            vpc_uuid="",
            well_known_uuid=WELL_KNOWN_UUIDS.APP_1.value,
        )
    ],
)
