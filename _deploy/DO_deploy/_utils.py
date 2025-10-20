import json
import logging
import os
from uuid import UUID

import structlog
from pydo import Client

from DO_deploy._DO_types import DropletResponse, IPVersion


def get_DO_token() -> str:
    token_env_var = "DIGITALOCEAN_TOKEN"  # noqa: S105 hardcoded-password-string
    token = os.getenv(token_env_var)

    if not token:
        raise ValueError(f"Env. var '{token_env_var}' not found or unset.")

    return token


def get_DO_client():
    """
    Click-ops for this to work:
    1. Create an API token <https://cloud.digitalocean.com/account/api/tokens>
        1. Set an expiration date
        2. Set Custom Scopes:
            - droplet: `create`, `update`, `delete`
            - ssh_key: `read`
            - tag: `create`
    """
    return Client(get_DO_token())


def get_wkid_from_tags(tags: list[str]) -> UUID | None:
    """Get well-known UUID from tags.
    Well-known UUIDs are defined at the top of every Blueprint file.
    """
    uuid_tags = [t for t in tags if t.startswith("wkid")]
    if not uuid_tags:
        return None
    return UUID(uuid_tags[0].split(":")[1])


def get_public_ip(
    droplet: DropletResponse, version: IPVersion | None = None
) -> str | None:
    if version is None:
        version = "v4"
    for net in droplet["networks"][version] + droplet["networks"]["v6"]:
        if net["type"] == "public":
            return net["ip_address"]
    return None


def configure_logging():
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(
                serializer=lambda obj, **kwargs: json.dumps(obj, ensure_ascii=False)
            ),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )
