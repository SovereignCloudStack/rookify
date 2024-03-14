# -*- coding: utf-8 -*-

from ..module import ModuleHandler, ModuleException

from typing import Any, Dict


class ExampleHandler(ModuleHandler):
    def preflight_check(self) -> None:
        # Do something for checking if all needed preconditions are met else throw ModuleException
        raise ModuleException("Example module was loaded, so aborting!")

    def run(self) -> Dict[str, Any]:
        # Run the migration tasks
        return {}
