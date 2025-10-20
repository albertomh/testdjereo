# Deploy a webapp from a container image by following a blue/green deployment stragegy.
#
# Assumes that the underlying infrastructure (and associated binaries) have been
# configured by a blueprint (see `infra/` & `infra/apply.py`).
#
# Usage:
#   ```sh
#   # run bare to see help message & full list of arguments
#   uv run python -m blue_green_deploy
#   ```
#
# Prerequisites:
#   Binaries that should be available locally:
#     - [ ] uv <https://docs.astral.sh/uv>
#     - [ ] wget
#   Data that needs to be passed to this script:
#     - [ ] A *classic* GitHub PAT with scope `read:packages`

import argparse
import dataclasses as dc
import logging
import subprocess
import sys
from argparse import RawTextHelpFormatter
from datetime import datetime
from enum import StrEnum, auto
from pathlib import Path
from typing import TypedDict

GHCR_BASE_URL = "ghcr.io"

LOG = logging.getLogger(__name__)


class DockerContainerInfo(TypedDict):
    ID: str
    Names: str
    Ports: str


@dc.dataclass
class Args:
    ghcr_username: str
    gh_pat: str
    docker_image: str
    container_name: str


class PortColour(StrEnum):
    BLUE = "8000"
    GREEN = "8080"


class ServerColour(StrEnum):
    BLUE = auto()
    GREEN = auto()


def set_up_logging():
    class PaddedFormatter(logging.Formatter):
        def format(self, record):
            record.levelname = record.levelname.ljust(len("WARNING"))
            record.asctime = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
            return f"{record.levelname} [{record.asctime}] {record.getMessage()}"

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    for h in logging.getLogger().handlers:
        h.setFormatter(PaddedFormatter())


def get_argument_parser() -> argparse.ArgumentParser:
    desc = (
        "Blue/green deployment for Dockerised web apps\n\n"
        "Spins up a new webapp container, waits for it to be healthy,\n"
        "has nginx forward requests to the new one and winds down the\n"
        "old container."
    )

    parser = argparse.ArgumentParser(
        prog=Path(__file__).name,
        usage="uv run python -m blue_green_deploy",
        description=desc,
        epilog="Text at the bottom of help",
        formatter_class=RawTextHelpFormatter,
    )

    parser.add_argument(
        "-u",
        "--ghcr-username",
        required=True,
        help="Username to authenticate against ghcr.io",
    )
    parser.add_argument(
        "-t",
        "--gh-pat",
        required=True,
        help="GitHub Personal Access Token. Must have scopes `repo`",
    )
    parser.add_argument(
        "-i",
        "--image",
        required=True,
        help="Path to a Docker image on ghcr.io eg. `albertomh/testdjereo:latest`",
    )
    parser.add_argument(
        "-n",
        "--name",
        required=True,
        help="Name for the container eg. `testdjereo`",
    )

    return parser


def validate_args(args: Args):
    if not (args.gh_pat.startswith("github_pat_") or args.gh_pat.startswith("ghp_")):
        raise ValueError("GitHub PAT [-t, --pat PAT] must start with 'github_pat_'")

    if "/" not in args.docker_image:
        raise ValueError(
            "Docker image [-i, --image] must be the path to a ghcr.io image"
        )


def create_docker_network(docker_network_name: str):
    existing_nets_res = subprocess.run(
        [  # noqa: S607 start-process-with-partial-path
            "docker",
            "network",
            "ls",
            "--format",
            "{{.Name}}",
        ],
        text=True,
        capture_output=True,
    )
    if f"{docker_network_name}\n" not in existing_nets_res.stdout:
        subprocess.run(
            [  # noqa: S607 start-process-with-partial-path
                "docker",
                "network",
                "create",
                docker_network_name,
            ],
        )


def log_in_to_github_container_registry(
    ghcr_username: str,
    gh_pat: str,
) -> None:
    result = subprocess.run(
        [  # noqa: S607 start-process-with-partial-path
            "docker",
            "login",
            "ghcr.io",
            "--username",
            ghcr_username,
            "--password",
            gh_pat,
        ],
        text=True,
        capture_output=True,
    )

    if result.returncode == 0:
        LOG.info("logged into ghcr.io")
    else:
        LOG.error("could not log into ghcr.io - check PAT passed as [-t, --gh-pat]")
        sys.exit(1)


def new_static_volume_for_next(container_name: str) -> str:
    now = datetime.now().strftime("%Y%m%dT%H%M%S")
    volume_name = f"{container_name}_static_{now}"
    try:
        subprocess.run(
            [
                "docker",
                "volume",
                "create",
            ],
            check=True,
        )
        LOG.info("created volume for static assets '%s'", volume_name)
        return volume_name
    except subprocess.CalledProcessError:
        LOG.error("failed to create volume for static assets '%s'", volume_name)
        sys.exit(1)


def get_containers_by_filter(filter_expr: str) -> list[DockerContainerInfo]:
    try:
        # eg. `3f...8d   <container_name>   0.0.0.0:8000->8000/tcp, :::8000->8000/tcp`
        result = subprocess.run(
            [
                "docker",
                "ps",
                "--format",
                "{{.ID}}\t{{.Names}}\t{{.Ports}}",
                "--filter",
                filter_expr,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        LOG.error("'docker ps' failed. Check the Docker service is running.")
        sys.exit(1)

    containers: list[DockerContainerInfo] = [
        {"ID": fields[0], "Names": fields[1], "Ports": fields[2]}
        for line in result.stdout.strip().splitlines()
        if (fields := line.split("\t"))
    ]
    return containers


def get_server_colours(container_name: str) -> tuple[ServerColour, ServerColour]:
    container_res = get_containers_by_filter(f"name=^{container_name}")

    if len(container_res) == 0:
        LOG.warning("no running container found for '%s'", container_name)
        cur_container: DockerContainerInfo = {
            "ID": "placeholderID",
            "Names": "tplaceholderName",
            "Ports": "0.0.0.0:8000->8000/tcp, :::8000->8000/tcp",
        }

    if len(container_res) > 1:
        LOG.error("found more than one '%s' container", container_name)
        sys.exit(1)

    cur_port_mapping = cur_container["Ports"]
    if f"{PortColour.BLUE.value}->{PortColour.BLUE.value}" in cur_port_mapping:
        cur_colour = ServerColour.BLUE
        next_colour = ServerColour.GREEN
    elif f"{PortColour.GREEN.value}->{PortColour.GREEN.value}" in cur_port_mapping:
        cur_colour = ServerColour.GREEN
        next_colour = ServerColour.BLUE
    else:
        LOG.error("could not establish next colour for '%s' container", container_name)
        sys.exit(1)

    LOG.info("current colour: %s, next colour: %s", cur_colour.value, next_colour.value)
    return cur_colour, next_colour


def create_next_app_container(
    *,
    docker_image: str,
    next_container_name: str,
    next_port: PortColour,
    next_static_volume: str,
) -> None:
    docker_image_path = f"{GHCR_BASE_URL}/{docker_image}"
    subprocess.run(
        # "--platform", "linux/amd64",
        ["docker", "image", "pull", docker_image_path],
        check=False,
    )

    result = subprocess.run(
        [
            "docker",
            "run",
            "--detach",
            "--name",
            next_container_name,
            "--user",
            "root",
            # "--env-file",
            # "/etc/testdjereo/.env",
            "--env",
            f"PORT={next_port.value}",
            "--network",
            "testdjereo_net",
            "--publish",
            f"{next_port.value}:{next_port.value}",
            "--volume",
            f"{next_static_volume}:/app/static",
            docker_image_path,
        ],
        capture_output=True,
    )

    if result.returncode == 0:
        LOG.info("created new container '%s'", next_container_name)
    else:
        LOG.error("failed to create new container '%s'", next_container_name)
        LOG.error(result.stderr.decode("utf-8"))
        sys.exit(1)


def run_django_migrations_in_next_container(next_container_name: str):
    result = subprocess.run(
        ["docker", "exec", next_container_name, "python", "manage.py", "migrate"],
        capture_output=True,
    )

    if result.returncode == 0:
        LOG.info("ran Django migrations in container '%s'", next_container_name)
    else:
        LOG.error(
            "error running Django migrations in container '%s'", next_container_name
        )
        sys.exit(1)


def container_is_healthy(
    *, port: PortColour, health_endpoint: str, expect_res: str
) -> bool:
    return False


def stop_and_remove_container(container_name: str):
    container = get_containers_by_filter(f"name={container_name}")

    if not container:
        LOG.warning("no running container found for '%s'", container_name)
        return

    result = subprocess.run(["docker", "stop", container_name], capture_output=True)
    if result.returncode == 0:
        LOG.info("stopped container '%s'", container_name)
    else:
        LOG.error("error stopping old container '%s'", container_name)
        sys.exit(1)

    result = subprocess.run(["docker", "rm", container_name], capture_output=True)
    if result.returncode == 0:
        LOG.info("removed container '%s'", container_name)
    else:
        LOG.error("error removing old container '%s'", container_name)
        sys.exit(1)


def main(args: Args):
    validate_args(args)

    docker_network_name = f"{args.container_name}_net"
    create_docker_network(docker_network_name)

    # create new app container -------------------------------------------------
    log_in_to_github_container_registry(args.ghcr_username, args.gh_pat)

    next_static_volume = new_static_volume_for_next(args.container_name)

    cur_server_colour, next_server_colour = get_server_colours(args.container_name)
    cur_container_name = f"{args.container_name}_{cur_server_colour.value}"
    next_container_name = f"{args.container_name}_{next_server_colour.value}"
    next_port = PortColour[next_server_colour.upper()]
    create_next_app_container(
        docker_image=args.docker_image,
        next_container_name=next_container_name,
        next_port=next_port,
        next_static_volume=next_static_volume,
    )
    run_django_migrations_in_next_container(next_container_name)

    if container_is_healthy(
        port=next_port, health_endpoint="/-/health/", expect_res='{"healthy": true}'
    ):
        LOG.info("next container '%s' is healthy", next_container_name)
    else:
        LOG.error("next container '%s' is not healthy", next_container_name)
        sys.exit(1)

    # configure nginx ----------------------------------------------------------

    # clean up -----------------------------------------------------------------

    stop_and_remove_container(cur_container_name)
    subprocess.run(
        ["docker", "volume", "prune", "--all", "--force"],
    )

    LOG.info("now serving from '%s:%s'", next_container_name, next_port)
    LOG.info("deployment done.")


if __name__ == "__main__":
    set_up_logging()

    parser = get_argument_parser()
    args_ns = parser.parse_args(args=None if sys.argv[1:] else ["--help"])
    args = Args(
        ghcr_username=args_ns.ghcr_username,
        gh_pat=args_ns.gh_pat,
        docker_image=args_ns.image,
        container_name=args_ns.name,
    )

    main(args)
