# -*- coding: utf-8 -*-

from typing import Dict, Any
from ..module import ModuleHandler


class MigrateMonitorsHandler(ModuleHandler):
    REQUIRES = ["analyze_ceph"]

    def run(self) -> Dict[str, Any]:
        self.logger.info("MigrateMonitorsHandler ran successfully.")
        return {}
