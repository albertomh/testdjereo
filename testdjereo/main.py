from importlib.metadata import version

import structlog

from testdjereo.logging import configure_logging

configure_logging()


def main():
    """Entrypoint for testdjereo."""
    logger = structlog.get_logger()
    logger.info("testdjereo v%s", version("testdjereo"))
    return


if __name__ == "__main__":
    main()
