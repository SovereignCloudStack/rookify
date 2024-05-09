# -*- coding: utf-8 -*-

from typing import Any, Dict
from ..machine import Machine
from ..module import ModuleException, ModuleHandler


class CephXAuthHandler(ModuleHandler):
    def preflight(self) -> Any:
        if not self.is_cephx_set(self.ceph.conf_get("auth_cluster_required")):
            raise ModuleException(
                "Ceph config value auth_cluster_required does not contain cephx"
            )

        if not self.is_cephx_set(self.ceph.conf_get("auth_service_required")):
            raise ModuleException(
                "Ceph config value auth_service_required does not contain cephx"
            )

        if not self.is_cephx_set(self.ceph.conf_get("auth_client_required")):
            raise ModuleException(
                "Ceph config value auth_client_required does not contain cephx"
            )

        self.machine.get_state("CephXAuthHandler").verified = True
        self.logger.info("Validated Ceph to expect cephx auth")

    def is_cephx_set(self, values: str) -> Any:
        return "cephx" in [value.strip() for value in values.split(",")]

    @classmethod
    def register_state(
        _, machine: Machine, config: Dict[str, Any], **kwargs: Any
    ) -> None:
        """
        Register state for transitions
        """

        super().register_state(machine, config, tags=["verified"])
