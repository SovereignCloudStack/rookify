# -*- coding: utf-8 -*-

from ..module import ModuleHandler
from typing import Any


class CephXAuthHandler(ModuleHandler):
    def run(self) -> Any:
        self.logger.debug("Reconfiguring Ceph to expect cephx auth")

        self.ceph.conf_set("auth_cluster_required", "cephx")
        self.ceph.conf_set("auth_service_required", "cephx")
        self.ceph.conf_set("auth_client_required", "cephx")

        self.logger.info("Reconfigured Ceph to expect cephx auth")
        return {"reconfigured": True}
