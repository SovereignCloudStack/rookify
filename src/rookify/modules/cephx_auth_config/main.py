# -*- coding: utf-8 -*-

from typing import Any, Dict
from ..exception import ModuleException
from ..machine import Machine
from ..module import ModuleHandler


class CephXAuthHandler(ModuleHandler):
    def preflight(self) -> None:
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

        self.machine.get_preflight_state("CephXAuthHandler").verified = True

        self.logger.info("Validated Ceph to expect cephx auth")

    def is_cephx_set(self, values: str) -> Any:
        return "cephx" in [value.strip() for value in values.split(",")]

    def get_readable_key_value_state(self) -> Dict[str, str]:
        is_verified = self.machine.get_preflight_state_data(
            "CephXAuthHandler", "verified", default_value=False
        )
        return {"cephx auth is verified": str(is_verified)}

    @staticmethod
    def register_preflight_state(
        machine: Machine, state_name: str, handler: ModuleHandler, **kwargs: Any
    ) -> None:
        ModuleHandler.register_preflight_state(
            machine, state_name, handler, tags=["verified"]
        )
