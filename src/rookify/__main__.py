# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from .modules import load_modules
from .modules.machine import Machine
from .logger import configure_logging, get_logger
from .yaml import load_config


def main() -> None:
    arg_parser = ArgumentParser("Rookify")
    arg_parser.add_argument("--dry-run", action="store_true", dest="dry_run_mode")
    args = arg_parser.parse_args()

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

    machine = Machine(config["general"].get("machine_pickle_file"))
    load_modules(machine, config)

    machine.execute(args.dry_run_mode)
