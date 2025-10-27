#
#
# Usage:
#   ```sh
#   uv run python -m \
#     DO_deploy.upload_deployment_script [-h] app_name {test,live} user
#   ```
#
# Prerequisites:
#   Binaries that should be available locally:
#     - [ ] uv <https://docs.astral.sh/uv>
#   Data that must be available to this script:
#     - [ ] A Digital Ocean token stored in env. var. `$DIGITALOCEAN__TOKEN`
#   Data this assumes exists:
#     - [ ] The `_deploy/` directory, including a top-level `.env` file

import argparse
import shlex
import subprocess
import sys
from pathlib import Path

import structlog
from pydo import Client as DO_Client

from DO_deploy._types import Environment
from DO_deploy._utils import (
    configure_logging,
    get_DO_client,
)
from DO_deploy.list_droplet_IPs import get_droplet_ips_for_env

# `_deploy/` ie. directory containing closest pyproject.toml
PACKAGE_ROOT = Path(__file__).resolve().parents[1]


configure_logging()
LOGGER = structlog.get_logger()


def main(*, do_client: DO_Client, app_name: str, env: Environment, user: str):
    target_dir = f"/etc/{app_name}/_deploy/"

    droplet_ips = get_droplet_ips_for_env(do_client, env, "v4")
    if droplet_ips:
        LOGGER.info("found Droplets to target", count=len(droplet_ips))

    for wkid, ip in droplet_ips.items():
        try:
            subprocess.run(
                [
                    "ssh",
                    "-vvv",
                    "-o",
                    "StrictHostKeyChecking=no",
                    f"{user}@{ip}",
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
            LOGGER.info(
                "created directory on host", target_dir=target_dir, wkid=str(wkid)
            )
        except subprocess.CalledProcessError:
            LOGGER.error(
                "failed to create directory on host",
                target_dir=target_dir,
                wkid=str(wkid),
            )
            sys.exit(1)

        # relative to `PACKAGE_ROOT` (tar+ssh changes directories before running below)
        # use relative paths, do NOT prepend with `PACKAGE_ROOT` in `files_to_upload`
        # as this would simply recreate the full absolute path in the VPS!
        files_to_upload = [
            ".env",
            "pyproject.toml",
            "DO_deploy/__init__.py",
            "DO_deploy/_types.py",
            "DO_deploy/_DO_types.py",
            "DO_deploy/_utils.py",
            "DO_deploy/deploy/",
        ]

        try:
            tar_cmd = ["tar", "czf", "-", *[str(f) for f in files_to_upload]]
            ssh_cmd = [
                "ssh",
                "-vvv",
                f"{user}@{ip}",
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
                "used tar + ssh to upload files to host",
                files_count=len(files_to_upload),
                wkid=str(wkid),
            )
        except subprocess.CalledProcessError:
            LOGGER.error(
                "failed to ssh files up to host", target_dir=target_dir, wkid=str(wkid)
            )
            sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "app_name",
        type=str,
        help="Name of the application, used to create `/etc/$app_name/` in target VPS",
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
    app_name = args.app_name
    env = args.env
    user = args.user

    do_client = get_DO_client()
    main(do_client=do_client, app_name=app_name, env=env, user=user)
