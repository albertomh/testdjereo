from dataclasses import dataclass
from typing import TypedDict

from DO_deploy._DO_types import DropletRequest
from DO_deploy._types import Environment, EnvVarDataClass


class EnvironmentBlueprint(TypedDict):
    environment: Environment
    droplets: list[DropletRequest]


@dataclass(frozen=True)
class PostgresServerEnv(EnvVarDataClass):
    ssh_public_key: str
    postgres_db: str
    postgres_user: str
    postgres_password: str


@dataclass(frozen=True)
class AppServerEnv(EnvVarDataClass):
    ssh_public_key: str
