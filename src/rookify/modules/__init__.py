# -*- coding: utf-8 -*-

import functools
import importlib

from typing import Optional
from collections import OrderedDict
from .module import ModuleHandler

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

def load_modules(module_names: list) -> list:
    """
    Dynamically loads modules from the 'modules' package.

    :param module_names: The module names to load
    """

    # Load the modules in the given list and recursivley load required modules
    required_modules = OrderedDict()
    def load_required_modules(module_names: list, modules: OrderedDict) -> None:
        for module_name in module_names:
            if module_name in modules:
                continue

            module = importlib.import_module(f"rookify.modules.{module_name}")

            for attr_type, attr_name in (
                (ModuleHandler, 'HANDLER_CLASS'),
                (str, 'MODULE_NAME'),
                (list, 'REQUIRES'),
                (list, 'AFTER'),
                (bool, 'RUN_IN_PREFLIGHT')
            ):
                if not hasattr(module, attr_name):
                    raise ModuleLoadException(module_name, f'Module has no attribute {attr_name}')

                attr = getattr(module, attr_name)
                if not isinstance(attr, attr_type) and not issubclass(attr, attr_type):
                    raise ModuleLoadException(module_name, f'Attribute {attr_name} is not type {attr_type}')

            load_required_modules(module.REQUIRES, modules)
            module.AFTER.extend(module.REQUIRES)

            modules[module_name] = module
    load_required_modules(module_names, required_modules)

    # Sort the modules by the AFTER keyword
    modules = OrderedDict()
    def sort_modules(modules_in: OrderedDict, modules_out: OrderedDict, module_names: list) -> None:
        for module_name in module_names:
            if module_name not in modules_in:
                continue

            if module_name in modules_out:
                continue

            after_modules_name = modules_in[module_name].AFTER
            sort_modules(modules_in, modules_out, after_modules_name)

            modules_out[module_name] = modules_in[module_name]
    sort_modules(required_modules, modules, list(required_modules.keys()))

    return list(modules.values())
