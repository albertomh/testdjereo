import json
import logging
import os
from pathlib import Path
from uuid import UUID

import structlog
from jinja2 import Template
from pydo import Client

from testdjereo_deploy._types import CloudConfigEnv


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


def render_cloud_config(name: str, env_vars: CloudConfigEnv) -> str:
    """Return the plain-text contents of a cloud-config YAML file, ready to be passed to
    the body of a `client.droplets.create()` call (ie. a DropletRequest object).
    """
    PACKAGE_ROOT = Path(__file__).resolve().parent
    template_path = PACKAGE_ROOT / "infra" / "cloud-config" / f"{name}.yaml.jinja"
    template_text = template_path.read_text(encoding="utf-8")
    return Template(template_text).render(**env_vars.as_dict())
