import logging
import sys
import os
import colorlog

from MAppServer.settings import LOG_DIR, FILE_LOGGING


def get(name: str, level=logging.INFO) -> logging.Logger:
    """Get the logger for the module name."""

    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        # Create console handler and set level to debug
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)

        # Create formatter
        formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(levelname)-8s%(reset)s %(message)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        )

        # Add formatter to ch
        ch.setFormatter(formatter)

        # Add ch to logger
        logger.addHandler(ch)

        # Add file handler
        if FILE_LOGGING:
            logger.addHandler(logging.FileHandler(f"{LOG_DIR}/{name}.log"))

    return logger


def main():
    """for demo purposes."""
    _LOG = get(__name__, level=logging.INFO)
    _LOG.info("tamere")
    _LOG.warning("tamere")
    _LOG.error("tamere")


if __name__ == "__main__":
    main()
