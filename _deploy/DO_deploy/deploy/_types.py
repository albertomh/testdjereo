from dataclasses import dataclass

from DO_deploy._types import EnvVarDataClass


@dataclass(frozen=True)
class AppServerDeployContext(EnvVarDataClass):
    app__debug: str
    app__secret_key: str
    app__allowed_hosts: str
    app__csrf_trusted_origins: str
    app__database_url: str
