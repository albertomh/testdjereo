import argparse
import logging
from pathlib import Path

from DO_deploy._types import Environment
from DO_deploy.infra._utils import set_up_logging

LOG = logging.getLogger(__name__)


def main(env: Environment):
    pass


if __name__ == "__main__":
    set_up_logging()

    parser = argparse.ArgumentParser(
        prog=Path(__file__).name,
        usage="uv run python -m check_deployment_health",
        description="",
    )

    parser.add_argument(
        "env",
        type=Environment,
        choices=list(Environment),
        help="Environment to run against",
    )
    args = parser.parse_args()
    env = args.env

    main(env)
