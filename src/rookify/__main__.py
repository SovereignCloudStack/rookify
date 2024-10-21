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

    arg_parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        dest="dry_run_mode",
        help="Preflight data analysis and migration validation.",
    )

    arg_parser.add_argument(
        "-m",
        "--migrate",
        action="store_true",
        dest="execution_mode",
        help="Run the migration.",
    )

    arg_parser.add_argument(
        "-s",
        "--show-states",
        action="store_true",
        dest="show_states",
        help="Show states of the modules.",
    )

    if len(args) < 1:
        args = ["--dry-run"]

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
        if args.show_states:
            configure_logging(
                {"level": "ERROR", "format": {"renderer": "console", "time": "iso"}}
            )
        else:
            configure_logging(config["logging"])
    except Exception as e:
        raise SystemExit(f"Error configuring logging: {e}")

    # Get Logger
    log = get_logger()

    machine = Machine(config["general"].get("machine_pickle_file"))

    load_modules(machine, config)

    if args.show_states:
        log.debug("Showing Rookify state ...")
        ModuleHandler.show_states(machine, config)
    elif args.dry_run_mode:
        log.info("Running Rookify in dry-run mode ...")
        machine.execute(dry_run_mode=args.dry_run_mode)
    else:
        log.info("Executing Rookify ...")
        machine.execute()


if __name__ == "__main__":
    main()
