# -*- coding: utf-8 -*-

import importlib
from typing import Any, Dict
from .machine import Machine


class ModuleLoadException(Exception):
    """
    ModuleLoadException is an exception class that can be raised during the dynamic load process for modules.
    """

    def __init__(self, module_name: str, message: str):
        """
        Construct a new 'ModuleLoadException' object.

        :param module_name: The name of the module the exception was raised for
        :param message: The message of the exception
        """
        self.module_name = module_name
        self.message = message


def _load_module(machine: Machine, config: Dict[str, Any], module_name: str) -> None:
    """
    Dynamically loads a module from the 'rookify.modules' package.

    :param module_names: The module names to load
    :return: returns tuple of preflight_modules, modules
    """

    module = importlib.import_module("rookify.modules.{0}".format(module_name))
    additional_modules = []

    if not hasattr(module, "ModuleHandler") or not callable(
        getattr(module.ModuleHandler, "register_states")
    ):
        raise ModuleLoadException(module_name, "Module structure is invalid")

    if hasattr(module.ModuleHandler, "REQUIRES"):
        assert isinstance(module.ModuleHandler.REQUIRES, list)
        additional_modules = module.ModuleHandler.REQUIRES

    for module_name in additional_modules:
        _load_module(machine, config, module_name)

    module.ModuleHandler.register_states(machine, config)


def load_modules(machine: Machine, config: Dict[str, Any]) -> None:
    """
    Dynamically loads modules from the 'modules' package.

    :param module_names: The module names to load
    :return: returns tuple of preflight_modules, modules
    """

    for entry in importlib.resources.files("rookify.modules").iterdir():
        if entry.is_dir() and entry.name in config["migration_modules"]:
            _load_module(machine, config, entry.name)
