from enum import Enum, StrEnum
from pathlib import Path
from uuid import UUID

from digitalocean_deployment_orchestrator.infra.types import (
    AppServerEnv,
    Environment,
    EnvironmentBlueprint,
)
from digitalocean_deployment_orchestrator.infra.utils import render_cloud_config
from digitalocean_deployment_orchestrator.types_cloudflare import DNSRecord
from digitalocean_deployment_orchestrator.types_DO import (
    DORegion,
    DropletImage,
    DropletRequest,
    DropletSize,
    IPAddressForDroplet,
)


class WELL_KNOWN_UUIDS(Enum):
    APP_1 = UUID("f57cebc7-3e29-4096-b1a6-c67d84a88019")
    DB_1 = UUID("6bd8663c-9e5d-4890-982f-cc5bffdd6001")


class SSH_KEYS(StrEnum):
    ID_ED25519 = "c1:e9:aa:64:23:92:ae:e3:2b:60:74:f3:cb:73:18:d3"


INFRA_DIR = Path(__file__).parents[1]
CLOUD_CONFIG_DIR = INFRA_DIR / "cloud_config_templates"

BLUEPRINT = EnvironmentBlueprint(
    #
    environment=Environment.TEST,
    #
    droplets=[
        DropletRequest(
            name="webapp-f57cebc7",
            region=DORegion.LONDON1,
            size=DropletSize.BASIC_YOCTO,
            image=DropletImage.DEBIAN_13_X64,
            ssh_keys=[SSH_KEYS.ID_ED25519.value],
            tags=[],
            user_data=render_cloud_config(
                CLOUD_CONFIG_DIR / "app_server.yaml.jinja", AppServerEnv.from_env()
            ),
            vpc_uuid="",
            well_known_uuid=WELL_KNOWN_UUIDS.APP_1.value,
        ),
        # DropletRequest(
        #     name="db-6bd8663c",
        #     region=DORegion.LONDON1,
        #     size=DropletSize.BASIC_YOCTO,
        #     image=DropletImage.DEBIAN_13_X64,
        #     ssh_keys=[SSH_KEYS.ID_ED25519.value],
        #     tags=[],
        #     user_data=render_cloud_config(
        #         CLOUD_CONFIG_DIR / "postgres_server.yaml.jinja",
        #         PostgresServerEnv.from_env(),
        #     ),
        #     vpc_uuid="",
        #     well_known_uuid=WELL_KNOWN_UUIDS.DB_1.value,
        # ),
    ],
    dns=[
        DNSRecord(
            cf_zone_name="crimecompass.com",
            type="A",
            name="@",
            content=IPAddressForDroplet(droplet_wkid=WELL_KNOWN_UUIDS.APP_1.value),
            proxied=True,
        ),
        DNSRecord(
            cf_zone_name="crimecompass.com",
            type="CNAME",
            name="www",
            content="crimecompass.com",
            proxied=True,
        ),
    ],
)
