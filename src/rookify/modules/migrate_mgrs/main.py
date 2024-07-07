# -*- coding: utf-8 -*-

from time import sleep
from typing import Any
from ..exception import ModuleException
from ..machine import Machine
from ..module import ModuleHandler


class MigrateMgrsHandler(ModuleHandler):
    REQUIRES = ["analyze_ceph", "create_cluster"]

    def execute(self) -> None:
        state_data = self.machine.get_preflight_state("AnalyzeCephHandler").data

        for node, _ in state_data["node"]["ls"]["mgr"].items():
            self._migrate_mgr(node)

    def _migrate_mgr(self, mgr_host: str) -> None:
        migrated_mgrs = getattr(
            self.machine.get_execution_state("MigrateMgrsHandler"), "migrated_mgrs", []
        )
        if mgr_host in migrated_mgrs:
            return

        self.logger.debug("Migrating Ceph mgr daemon '{0}'".format(mgr_host))

        result = self.ssh.command(
            mgr_host, "sudo systemctl disable --now ceph-mgr.target"
        )

        if result.failed:
            raise ModuleException(
                "Disabling original Ceph mgr daemon at host {0} failed: {1}".format(
                    mgr_host, result.stderr
                )
            )

        self.logger.debug(
            "Waiting for disabled original Ceph mgr daemon '{0}' to disconnect".format(
                mgr_host
            )
        )

        while True:
            result = self.ceph.mon_command("node ls")

            if mgr_host not in result["mgr"]:
                break

            sleep(2)

        self.logger.info(
            "Disabled Ceph mgr daemon '{0}' and enabling Rook based Ceph mgr daemon '{0}'".format(
                mgr_host
            )
        )

        node_patch = {"metadata": {"labels": {self.k8s.mgr_placement_label: "enabled"}}}

        if (
            self.k8s.mgr_placement_label
            not in self.k8s.core_v1_api.patch_node(mgr_host, node_patch).metadata.labels
        ):
            raise ModuleException(
                "Failed to patch k8s node for Ceph mgr daemon '{0}'".format(mgr_host)
            )

        migrated_mgrs.append(mgr_host)

        self.machine.get_execution_state(
            "MigrateMgrsHandler"
        ).migrated_mgrs = migrated_mgrs

        self.logger.debug("Waiting for 3 Ceph mgr daemons to be available")

        while True:
            result = self.ceph.mon_command("node ls")
            if len(result["mgr"]) >= 3:
                break

            sleep(2)

        self.logger.debug("3 Ceph mgr daemons are available")

    @staticmethod
    def register_execution_state(
        machine: Machine, state_name: str, handler: ModuleHandler, **kwargs: Any
    ) -> None:
        ModuleHandler.register_execution_state(
            machine, state_name, handler, tags=["migrated_mgrs"]
        )
