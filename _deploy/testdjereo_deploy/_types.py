import os
from dataclasses import dataclass, fields
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
    # the fingerprint(s) of SSH keys to embed in the Droplet's root account
    ssh_keys: list[str]
    backups: NotRequired[bool]
    ipv6: NotRequired[bool]
    monitoring: NotRequired[bool]
    # `user_data` should be the contents of a 'cloud-config' file
    # <https://www.digitalocean.com/community/tutorials/an-introduction-to-cloud-config-scripting>
    user_data: str
    well_known_uuid: UUID


class DropletResponse(BaseDroplet):
    """
    <https://docs.digitalocean.com/reference/api/digitalocean/#tag/Droplets>
    """

    id: int
    created_at: str


class DropletCreateResponse(TypedDict):
    droplet: DropletResponse
    links: dict


class DropletListResponse(TypedDict):
    droplets: list[DropletResponse]
    links: dict
    meta: MetaApiRes


# --- cloud-init / #cloud-config types ---------------------------------------------------


@dataclass(frozen=True)
class CloudConfigEnv:
    """
    Base class for all environment-variable-backed #cloud-configs.
    Subclasses must define fields that map to environment variables.
    """

    @classmethod
    def from_env(cls):
        """
        Load and validate all required environment variables.
        Raises EnvironmentError if any are missing.
        """
        missing = []
        values = {}

        for f in fields(cls):
            env_name = f.name.upper()
            val = os.getenv(env_name)
            if not val:
                missing.append(env_name)
            else:
                values[f.name] = val

        if missing:
            raise OSError(
                f"Missing environment variables for {cls.__name__}: {', '.join(missing)}"
            )

        return cls(**values)

    def as_dict(self) -> dict[str, str]:
        return {f.name: getattr(self, f.name) for f in fields(self)}


@dataclass(frozen=True)
class PostgresServerEnv(CloudConfigEnv):
    postgres_db: str
    postgres_user: str
    postgres_password: str


@dataclass(frozen=True)
class AppServerEnv(CloudConfigEnv):
    debug: str
    secret_key: str
    allowed_hosts: str
    csrf_trusted_origins: str
    database_url: str


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
