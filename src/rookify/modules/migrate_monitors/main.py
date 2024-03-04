# -*- coding: utf-8 -*-

from ..module import ModuleHandler
from rookify.logger import getLogger


class MigrateMonitorsHandler(ModuleHandler):
    def run(self):
        log = getLogger()
        log.info("MigrateMonitorsHandler ran successfully.")
    
