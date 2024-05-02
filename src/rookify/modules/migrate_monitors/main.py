# -*- coding: utf-8 -*-

from ..module import ModuleHandler
from typing import Dict, Any


class MigrateMonitorsHandler(ModuleHandler):
    def run(self) -> Dict[str, Any]:
        self.logger.info("MigrateMonitorsHandler ran successfully.")
        return {}
