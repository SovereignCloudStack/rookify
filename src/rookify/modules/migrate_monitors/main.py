# -*- coding: utf-8 -*-

from ..module import ModuleHandler


class MigrateMonitorsHandler(ModuleHandler):
    REQUIRES = ["analyze_ceph"]

    def execute(self) -> None:
        self.logger.info("MigrateMonitorsHandler ran successfully.")
