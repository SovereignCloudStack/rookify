# -*- coding: utf-8 -*-

from .modules import load_modules
from .modules.machine import Machine
from .logger import configure_logging, get_logger
from .yaml import load_config


def main() -> None:
    # Load configuration file
    try:
        config = load_config("config.yaml")
    except FileNotFoundError as err:
        raise SystemExit(f"Could not load config: {err}")

    # Configure logging
    try:
        configure_logging(config["logging"])
    except Exception as e:
        raise SystemExit(f"Error configuring logging: {e}")

    log = get_logger()
    log.debug("Executing Rookify")

    machine = Machine(config["general"]["machine_pickle_file"])
    load_modules(machine, config)

    machine.execute()
