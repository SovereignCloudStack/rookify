# -*- coding: utf-8 -*-

from ..module import ModuleHandler, ModuleException

from typing import Any


class ExampleHandler(ModuleHandler):
    def preflight(self) -> None:
        # Do something for checking if all needed preconditions are met else throw ModuleException
        raise ModuleException("Example module was loaded, so aborting!")

    def run(self) -> Any:
        # Run the migration tasks
        return {}
