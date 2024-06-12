# -*- coding: utf-8 -*-

from typing import Any
from ..exception import ModuleException
from ..module import ModuleHandler


class ExampleHandler(ModuleHandler):
    # A list of modules that are required to run the preflight_check of this module. Modules in this list will be imported and run in preflight stage.
    REQUIRES = ["analyze_ceph"]

    def preflight(self) -> None:
        # Do something for checking if all needed preconditions are met else throw ModuleException
        raise ModuleException("Example module was loaded, so aborting!")

    def execute(self) -> Any:
        # Run the migration tasks
        return {}
