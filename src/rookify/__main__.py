# -*- coding: utf-8 -*-

import sys
import argparse
from argparse import ArgumentParser
from typing import Any, Dict
from .modules import load_modules
from .modules.machine import Machine
from .modules.module import ModuleHandler
from .logger import configure_logging, get_logger
from .yaml import load_config


def parse_args(args: list[str]) -> argparse.Namespace:
    # Putting args-parser in seperate function to make this testable
    arg_parser = ArgumentParser("Rookify")

    arg_parser.add_argument("-d", "--dry-run", action="store_true", dest="dry_run_mode")

    arg_parser.add_argument(
        "-s",
        "--show-states",
        action="store_true",
        dest="show_states",
        help="Show states of the modules.",
    )

    arg_parser.add_argument(
        "run",
        nargs="?",
        default=False,
        help="Run the migration.",
    )

    # Show help if no arguments are provided
    if not args:
        arg_parser.print_help()
        sys.exit(1)

    return arg_parser.parse_args(args)


def main() -> None:
    args = parse_args(sys.argv[1:])

    # Load configuration file
    try:
        config: Dict[str, Any] = load_config("config.yaml")
    except FileNotFoundError as err:
        raise SystemExit(f"Could not load config: {err}")

    # Configure logging
    try:
        if args.show_states is True:
            configure_logging(
                {"level": "ERROR", "format": {"renderer": "console", "time": "iso"}}
            )
        else:
            configure_logging(config["logging"])
    except Exception as e:
        raise SystemExit(f"Error configuring logging: {e}")

    # Get Logger
    log = get_logger()

    log.info("Executing Rookify ...")

    machine = Machine(config["general"].get("machine_pickle_file"))

    load_modules(machine, config)

    if args.show_states is True:
        ModuleHandler.show_states(machine, config)
    if args.run:
        machine.execute(dry_run_mode=args.dry_run_mode)


if __name__ == "__main__":
    main()
