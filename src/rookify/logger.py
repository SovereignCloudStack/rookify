import structlog
import logging

from typing import Any, Dict


def configure_logging(config: Dict[str, Any]) -> None:
    LOG_LEVEL = getattr(logging, config["level"], logging.INFO)
    LOG_TIME_FORMAT = config["format"]["time"]
    LOG_RENDERER = config["format"]["renderer"]

    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(LOG_LEVEL),
        processors=[
            structlog.processors.TimeStamper(fmt=LOG_TIME_FORMAT),
            structlog.processors.add_log_level,
        ],
    )

    if LOG_RENDERER == "console":
        structlog.configure(
            processors=[
                *structlog.get_config()["processors"],
                structlog.dev.ConsoleRenderer(),
            ]
        )
    else:
        structlog.configure(
            processors=[
                *structlog.get_config()["processors"],
                structlog.processors.JSONRenderer(),
            ]
        )


def get_logger() -> structlog.getLogger:
    return structlog.get_logger()
