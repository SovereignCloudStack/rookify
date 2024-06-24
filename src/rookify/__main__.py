# -*- coding: utf-8 -*-

import sys
from argparse import ArgumentParser, Namespace
from .modules import load_modules
from .modules.machine import Machine
from .logger import configure_logging, get_logger
from .yaml import load_config


def parse_args(args: list[str]) -> Namespace:
    # Putting args-parser in seperate function to make this testable
    arg_parser = ArgumentParser("Rookify")
    arg_parser.add_argument("--dry-run", action="store_true", dest="dry_run_mode")
    arg_parser.add_argument(
        "--show",
        action="store_true",
        dest="show_progress",
        help="Show the current state of progress, as read from the pickle file",
    )
    return arg_parser.parse_args(args)


def main() -> None:
    args = parse_args(sys.argv[1:])

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

    machine.execute(dry_run_mode=args.dry_run_mode, show_progress=args.show_progress)
