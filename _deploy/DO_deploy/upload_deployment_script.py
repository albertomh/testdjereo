#
#
# Usage:
#   ```sh
#   uv run python -m \
#     DO_deploy.upload_deployment_script [-h] app_name {test,live} user
#   ```
#
# Prerequisites:
#

import argparse
import shlex
import subprocess
import sys
from pathlib import Path

import structlog
from pydo import Client as DO_Client

from DO_deploy._DO_types import DropletListResponse, DropletResponse
from DO_deploy._types import Environment
from DO_deploy._utils import (
    configure_logging,
    get_DO_client,
    get_public_ip,
)

# `_deploy/` ie. closest pyproject.toml
PACKAGE_ROOT = Path(__file__).resolve().parent.parent


configure_logging()
LOGGER = structlog.get_logger()


def main(*, client: DO_Client, app_name: str, env: Environment, user: str):
    droplets_res: DropletListResponse = client.droplets.list(tag_name=env.tag)
    droplets: list[DropletResponse] = droplets_res["droplets"]

    target_dir = f"/etc/{app_name}/_deploy/"
    for d in droplets:
        ip_v4_address = get_public_ip(d)
        try:
            subprocess.run(
                [
                    "ssh",
                    "-o",
                    "StrictHostKeyChecking=no",
                    f"{user}@{ip_v4_address}",
                    "--",
                    "sudo",
                    "mkdir",
                    "-p",
                    target_dir,
                    "&&",
                    "sudo",
                    "chown",
                    f"{user}:{user}",
                    target_dir,
                ],
                check=True,
            )
            LOGGER.info("created directory on host", target_dir=target_dir)
        except subprocess.CalledProcessError:
            LOGGER.error("failed to create directory on host", target_dir=target_dir)
            sys.exit(1)

        files_to_upload = [
            "pyproject.toml",
            "DO_deploy/__init__.py",
            "DO_deploy/_types.py",
            "DO_deploy/_DO_types.py",
            "DO_deploy/_utils.py",
            "DO_deploy/deploy/",
        ]

        try:
            tar_cmd = ["tar", "czf", "-", *files_to_upload]
            ssh_cmd = [
                "ssh",
                f"{user}@{ip_v4_address}",
                f"mkdir -p {target_dir} && tar xzf - -C {target_dir}",
            ]

            tar_and_ssh_cmd = (
                f"cd {PACKAGE_ROOT} && {shlex.join(tar_cmd)} | {shlex.join(ssh_cmd)}"
            )
            subprocess.run(  # noqa: S602 S603
                tar_and_ssh_cmd,
                shell=True,
                check=True,
            )
            LOGGER.info(
                "used ssh & tar to upload files to host",
                files_count=len(files_to_upload),
            )
        except subprocess.CalledProcessError:
            LOGGER.error("failed to scp files to host", target_dir=target_dir)
            sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "app_name",
        type=str,
        help="Name of the application, used to generate `/etc/$app_name` in target VPS",
    )
    parser.add_argument(
        "env",
        type=Environment,
        choices=list(Environment),
        help="Environment to run against",
    )
    parser.add_argument(
        "user",
        type=str,
        help="User to log into the VPS as",
    )
    args = parser.parse_args()
    env = args.env
    app_name = args.app_name
    user = args.user

    client = get_DO_client()
    main(client=client, app_name=app_name, env=env, user=user)
