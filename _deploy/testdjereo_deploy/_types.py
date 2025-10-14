from enum import StrEnum, auto
from typing import NotRequired, TypedDict
from uuid import UUID


# --- Digital Ocean-specific types -------------------------------------------------------
class MetaApiRes(TypedDict):
    total: int


class DORegion(StrEnum):
    LONDON1 = "lon1"


class DropletSize(StrEnum):
    """<https://www.nist.gov/pml/owm/metric-si-prefixes>"""

    BASIC_YOCTO = "s-1vcpu-512mb-10gb"  # $4/mo
    BASIC_ZEPTO = "s-1vcpu-1gb"  # $6/mo


class DropletImage(StrEnum):
    DEBIAN_12_X64 = "debian-12-x64"
    DEBIAN_13_X64 = "debian-13-x64"
    UBUNTU_2404_X64 = "ubuntu-24-04-x64"
    UBUNTU_2504_X64 = "ubuntu-25-04-x64"


class BaseDroplet(TypedDict):
    name: str
    tags: list[str]
    vpc_uuid: str


class DropletRequest(BaseDroplet):
    """
    <https://docs.digitalocean.com/reference/api/digitalocean/#tag/Droplets/operation/droplets_create>
    """

    region: DORegion
    size: DropletSize
    image: DropletImage
    ssh_keys: list
    backups: NotRequired[bool]
    ipv6: NotRequired[bool]
    monitoring: NotRequired[bool]
    user_data: str
    well_known_uuid: UUID


class DropletResponse(BaseDroplet):
    """
    <https://docs.digitalocean.com/reference/api/digitalocean/#tag/Droplets>
    """

    id: int
    created_at: str


class DropletListResponse(TypedDict):
    droplets: list[DropletResponse]
    links: dict
    meta: MetaApiRes


# --- Application types ------------------------------------------------------------------


class Environment(StrEnum):
    TEST = auto()
    LIVE = auto()

    @property
    def tag(self):
        return f"env:{self.value}"


class EnvironmentBlueprint(TypedDict):
    environment: Environment
    droplets: list[DropletRequest]
