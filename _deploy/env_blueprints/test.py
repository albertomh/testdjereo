from enum import Enum
from pathlib import Path
from uuid import UUID

from digitalocean_deployment_orchestrator.infra.types import (
    AppServerEnv,
    DropletDNSRecord,
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
)


class WELL_KNOWN_UUIDS(Enum):
    APP_1 = UUID("f57cebc7-3e29-4096-b1a6-c67d84a88019")
    DB_1 = UUID("6bd8663c-9e5d-4890-982f-cc5bffdd6001")


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
            ssh_keys=["c1:e9:aa:64:23:92:ae:e3:2b:60:74:f3:cb:73:18:d3"],
            tags=[],
            user_data=render_cloud_config(
                CLOUD_CONFIG_DIR / "app_server.yaml.jinja", AppServerEnv.from_env()
            ),
            vpc_uuid="",
            well_known_uuid=WELL_KNOWN_UUIDS.APP_1.value,
        ),
        # DropletRequest(
        #    name="db-6bd8663c",
        #    region=DORegion.LONDON1,
        #    size=DropletSize.BASIC_YOCTO,
        #    image=DropletImage.DEBIAN_13_X64,
        #    ssh_keys=[SSH_KEYS.id_ed25519],
        #    tags=[],
        #    user_data=render_cloud_config(
        #        "postgres_server", PostgresServerEnv.from_env()
        #    ),
        #    vpc_uuid="",
        #    well_known_uuid=WELL_KNOWN_UUIDS.DB_1.value,
        # ),
    ],
    dns=[
        DropletDNSRecord(
            droplet_wkid=WELL_KNOWN_UUIDS.APP_1.value,
            dns_record=DNSRecord(
                zone_id="19bd0c440c9b949b599203d8cbef5505",
                record_name="www.crimecompass.com",
                proxied=True,
            ),
        )
    ],
)
