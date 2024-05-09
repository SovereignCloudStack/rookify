# -*- coding: utf-8 -*-

from typing import Any
from ..module import ModuleHandler, ModuleException


class ExampleHandler(ModuleHandler):
    # A list of modules that are required to run the preflight_check of this module. Modules in this list will be imported and run in preflight stage.
    PREFLIGHT_REQUIRES = ["analyze_ceph"]

    def preflight(self) -> None:
        # Do something for checking if all needed preconditions are met else throw ModuleException
        raise ModuleException("Example module was loaded, so aborting!")

    def run(self) -> Any:
        # Run the migration tasks
        return {}
