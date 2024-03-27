# -*- coding: utf-8 -*-

from ..module import ModuleHandler
from rookify.logger import getLogger
from typing import Dict, Any


class MigrateMonitorsHandler(ModuleHandler):
    def run(self) -> Dict[str, Any]:
        log = getLogger()
        log.info("MigrateMonitorsHandler ran successfully.")
        return {}
