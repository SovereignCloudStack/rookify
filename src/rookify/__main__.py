# -*- coding: utf-8 -*-

from pickle import Unpickler
import sys
from argparse import ArgumentParser, Namespace
from typing import Any
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


def load_pickler(pickle_file_name: str) -> Any:
    with open(pickle_file_name, "ab+") as pickle_file:
        pickle_file.seek(0)
        states_data = Unpickler(pickle_file).load()
        return states_data


def sort_pickle_file(states_data: Any) -> Any:
    # sort the pickle-file alfabetically
    sorted_data_by_keys = dict(sorted(states_data))
    return sorted_data_by_keys


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

    # Get Pickle File if configured in config.yaml
    pickle_file_name = config["general"].get("machine_pickle_file")
    if pickle_file_name is None:
        log.info("No pickle file was set in the configuration.")
    else:
        log.info(f"Pickle file set: {pickle_file_name}")

    # If show_progress is true and pickle_file_name  is not None, show the current progress of the migration
    if args.show_progress:
        if pickle_file_name is None:
            return
        states_data = load_pickler(pickle_file_name)
        get_logger().info(
            "Current state as retrieved from pickle-file: {0}".format(states_data)
        )
    # Else run the rook migration
    else:
        log.debug("Executing Rookify")

        machine = Machine(pickle_file_name)
        load_modules(machine, config)

        machine.execute(dry_run_mode=args.dry_run_mode)
