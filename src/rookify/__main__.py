# -*- coding: utf-8 -*-

import json
from pickle import Unpickler
import sys
import argparse
from argparse import ArgumentParser, Namespace
from typing import Any, Dict, Optional
from .modules import load_modules
from .modules.machine import Machine
from .logger import configure_logging, get_logger
from .yaml import load_config


def parse_args(args: list[str]) -> Namespace:
    # Putting args-parser in seperate function to make this testable
    arg_parser = ArgumentParser("Rookify")
    arg_parser.add_argument("--dry-run", action="store_true", dest="dry_run_mode")

    # Custom ShowAction to set 'all' if nothing is specified for --show
    class ShowAction(argparse.Action):
        def __call__(
            self,
            parser: ArgumentParser,
            namespace: Namespace,
            values: Optional[Any],
            option_string: Optional[str] = None,
        ) -> None:
            setattr(namespace, self.dest, values if values is not None else "all")

    arg_parser.add_argument(
        "--show",
        nargs="?",
        action=ShowAction,
        dest="show_progress",
        metavar="<section>",
        help="Show the state of progress, as read from the pickle file. Default argument is 'all', you can also specify a section you want to look at.",
        required=False,
    )
    return arg_parser.parse_args(args)


def load_pickler(pickle_file_name: str) -> Any:
    with open(pickle_file_name, "ab+") as pickle_file:
        pickle_file.seek(0)
        states_data = Unpickler(pickle_file).load()
        return states_data


def sort_pickle_file(unsorted_states_data: Dict[str, Any]) -> Dict[str, Any]:
    # sort the pickle-file alfabetically
    iterable_dict = iter(unsorted_states_data)
    first_key = next(iterable_dict)
    data_values = unsorted_states_data[first_key]["data"]
    sorted_data_by_keys = {k: data_values[k] for k in sorted(data_values)}
    return sorted_data_by_keys


def main() -> None:
    args = parse_args(sys.argv[1:])

    # Load configuration file
    try:
        config: Dict[str, Any] = load_config("config.yaml")
    except FileNotFoundError as err:
        raise SystemExit(f"Could not load config: {err}")

    # Configure logging
    try:
        configure_logging(config["logging"])
    except Exception as e:
        raise SystemExit(f"Error configuring logging: {e}")
    # Get Logger
    log = get_logger()

    # Get Pickle File if configured in config.yaml
    pickle_file_name = config["general"].get("machine_pickle_file")
    if pickle_file_name is None:
        log.info("No pickle file was set in the configuration.")
    else:
        log.info(f"Pickle file set: {pickle_file_name}")

    # Get Pickle File if configured in config.yaml
    pickle_file_name = config["general"].get("machine_pickle_file")
    if pickle_file_name is None:
        log.info("No pickle file was set in the configuration.")
    else:
        log.info(f"Pickle file set: {pickle_file_name}")

    # If show_progress is not None and pickle_file_name is not None, show the current progress of the migration
    if args.show_progress is not None:
        if pickle_file_name is None:
            return
        states_data = load_pickler(pickle_file_name)
        sorted_states_data = sort_pickle_file(states_data)

        # Check if a specific section should be listed
        if args.show_progress != "all":
            if args.show_progress not in sorted_states_data.keys():
                get_logger().error(f"The section {args.show_progress} does not exist")
                return
            else:
                sorted_states_data = sorted_states_data[args.show_progress]

        get_logger().info(
            'Current state as retrieved from pickle-file: \n "{0}": {1}'.format(
                args.show_progress, json.dumps(sorted_states_data, indent=4)
            )
        )
    # Else run the rook migration
    else:
        log.debug("Executing Rookify")

        machine = Machine(config["general"].get("machine_pickle_file"))
        load_modules(machine, config)

        machine.execute(dry_run_mode=args.dry_run_mode)
