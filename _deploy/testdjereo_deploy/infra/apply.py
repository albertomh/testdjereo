import argparse
import copy
import importlib
import json
import pkgutil
import pprint
from types import ModuleType

import structlog
from pydo import Client as DO_Client

from testdjereo_deploy._types import (
    DropletCreateResponse,
    DropletListResponse,
    DropletRequest,
    DropletResponse,
    Environment,
    EnvironmentBlueprint,
)
from testdjereo_deploy._utils import configure_logging, get_DO_client, get_wkid_from_tags

configure_logging()
LOGGER = structlog.get_logger()


def load_environment_blueprint(env: Environment) -> EnvironmentBlueprint:
    """Load the blueprint for a given environment and ensure resources are tagged."""

    def _tag_resources(blueprint: EnvironmentBlueprint) -> EnvironmentBlueprint:
        bp = copy.deepcopy(blueprint)
        bp_env = bp["environment"]

        droplets = bp["droplets"]
        for d in droplets:
            env_tag = f"env:{bp_env.value}"
            wkid_tag = f"wkid:{d['well_known_uuid']}"
            d["tags"].extend([env_tag, wkid_tag])

        return bp

    import testdjereo_deploy.infra.blueprints as bp_pkg

    blueprints = []

    for module_info in pkgutil.iter_modules(bp_pkg.__path__):
        module_name = f"{bp_pkg.__name__}.{module_info.name}"
        module: ModuleType = importlib.import_module(module_name)

        if not hasattr(module, "BLUEPRINT"):
            LOGGER.warning("Skipping module with no BLUEPRINT", module=module_name)
            continue

        bp = module.BLUEPRINT

        if bp["environment"] == env:
            blueprints.append(bp)
            LOGGER.info(
                "Loaded blueprint",
                module=module_name,
                environment=bp["environment"].value,
            )

    if not blueprints:
        raise RuntimeError(
            f"No blueprints found for env:{env.value} in 'infra/blueprints/'"
        )

    if len(blueprints) != 1:
        raise ValueError(f"Multiple blueprints found for env:{env.value}")

    bp = _tag_resources(blueprints[0])
    return bp


def manage_droplets(
    is_dry_run: bool,
    client: DO_Client,
    env: Environment,
    blueprint_droplets: list[DropletRequest],
):
    actual_droplets_res: DropletListResponse = client.droplets.list(tag_name=env.tag)
    actual_droplets: list[DropletResponse] = actual_droplets_res["droplets"]
    future_droplets: list[DropletRequest] = copy.deepcopy(blueprint_droplets)
    actual_droplet_uuids = {get_wkid_from_tags(d["tags"]) for d in actual_droplets}
    future_droplet_uuids = {get_wkid_from_tags(d["tags"]) for d in future_droplets}
    # droplet_count = actual_droplets["meta"]["total"] - len(future_droplets)

    existing = actual_droplet_uuids & future_droplet_uuids
    to_create = future_droplet_uuids - actual_droplet_uuids
    to_destroy = actual_droplet_uuids - future_droplet_uuids

    LOGGER.info(
        "Droplet comparison",
        existing=len(existing),
        to_create=len(to_create),
        to_destroy=len(to_destroy),
    )

    if not to_create and not to_destroy:
        LOGGER.info(
            "Droplets in environment already match blueprint", environment=env.value
        )
        return

    def _create_droplet(droplet_req: DropletRequest):
        try:
            # deep copy + convert UUIDs
            safe_req = json.loads(json.dumps(droplet_req, default=str))
            res: DropletCreateResponse = client.droplets.create(body=safe_req)
        except Exception as err:
            LOGGER.error("Error creating Droplet", err=str(err))
            raise err
        else:
            wkid = get_wkid_from_tags(droplet_req["tags"])
            LOGGER.info("Created Droplet", wkid=str(wkid), id=res["droplet"]["id"])

    if to_create:
        LOGGER.info("Droplets to create", uuids=[str(id) for id in to_create])
        for droplet_req in future_droplets:
            redacted_droplet = {
                k: (v if k != "user_data" else "***REDACTED***")
                for k, v in droplet_req.items()
            }
            if is_dry_run:
                print("Would create Droplet:")  # noqa: T201
                pprint.pp(redacted_droplet)
            else:
                wkid = get_wkid_from_tags(droplet_req["tags"])
                if wkid in to_create:
                    _create_droplet(droplet_req)

    def _destroy_droplet(droplet_id: int):
        try:
            client.droplets.destroy(droplet_id=droplet_id)
        except Exception as err:
            LOGGER.error("Failed to destroy Droplet", err=str(err))
            raise err
        else:
            LOGGER.info("Destroyed Droplet", wkid=str(wkid), id=droplet_id)

    if to_destroy:
        LOGGER.info("Droplets to destroy", uuids=[str(id) for id in to_destroy])
        if not is_dry_run:
            for droplet in actual_droplets:
                wkid = get_wkid_from_tags(droplet["tags"])
                if wkid in to_destroy:
                    _destroy_droplet(droplet["id"])


def apply(is_dry_run: bool, client: DO_Client, env: Environment):
    blueprint: EnvironmentBlueprint = load_environment_blueprint(env)
    blueprint_droplets = blueprint["droplets"]
    manage_droplets(is_dry_run, client, env, blueprint_droplets)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "env",
        type=Environment,
        choices=list(Environment),
        help="Environment to run against",
    )
    parser.add_argument(
        "--no-dry-run",
        required=False,
        action="store_true",
        help="Actually apply blueprint to environment",
    )
    args = parser.parse_args()
    env = args.env
    is_dry_run = not args.no_dry_run
    LOGGER.info("Running DODO", environment=env.value)

    client = get_DO_client()
    apply(is_dry_run, client, env)
