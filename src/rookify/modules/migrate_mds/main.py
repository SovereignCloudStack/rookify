# -*- coding: utf-8 -*-

from time import sleep
from typing import Any
from ..exception import ModuleException
from ..machine import Machine
from ..module import ModuleHandler


class MigrateMdsHandler(ModuleHandler):
    REQUIRES = ["migrate_mds_pools"]

    def preflight(self) -> None:
        migrated_mds = self.machine.get_execution_state_data(
            "MigrateMdsHandler", "migrated_mds", default_value=[]
        )

        if len(migrated_mds) > 0:
            return

        self.k8s.check_nodes_for_initial_label_state(self.k8s.mds_placement_label)

        state_data = self.machine.get_preflight_state("AnalyzeCephHandler").data

        for node, mds_daemons in state_data["node"]["ls"]["mds"].items():
            if len(mds_daemons) > 1:
                raise ModuleException(
                    "There are more than 1 Ceph mds daemons running on node {0}".format(
                        node
                    )
                )

    def execute(self) -> None:
        state_data = self.machine.get_preflight_state("AnalyzeCephHandler").data

        for node in state_data["node"]["ls"]["mds"].keys():
            self._migrate_mds(node)

    def _migrate_mds(self, mds_host: str) -> None:
        migrated_mds = self.machine.get_execution_state_data(
            "MigrateMdsHandler", "migrated_mds", default_value=[]
        )
        if mds_host in migrated_mds:
            return

        self.logger.debug("Migrating Ceph mds daemon '{0}'".format(mds_host))

        migrated_mds_pools = self.machine.get_execution_state_data(
            "MigrateMdsPoolsHandler", "migrated_mds_pools", default_value=[]
        )
        is_migration_required = len(migrated_mds_pools) > 0

        if is_migration_required:
            result = self.ssh.command(
                mds_host, "sudo systemctl disable --now ceph-mds.target"
            )

            if result.failed:
                raise ModuleException(
                    "Disabling original Ceph mds daemon at host {0} failed: {1}".format(
                        mds_host, result.stderr
                    )
                )

            self.logger.debug(
                "Waiting for disabled original Ceph mds daemon '{0}' to disconnect".format(
                    mds_host
                )
            )

            while True:
                result = self.ceph.mon_command("node ls")

                if mds_host not in result["mds"]:
                    break

                sleep(2)

            self.logger.info(
                "Disabled Ceph mds daemon '{0}' and enabling Rook based Ceph mds daemon '{0}'".format(
                    mds_host
                )
            )

        node_patch = {"metadata": {"labels": {self.k8s.mds_placement_label: "true"}}}

        if (
            self.k8s.mds_placement_label
            not in self.k8s.core_v1_api.patch_node(mds_host, node_patch).metadata.labels
        ):
            raise ModuleException(
                "Failed to patch k8s node for Ceph mds daemon '{0}'".format(mds_host)
            )

        migrated_mds.append(mds_host)

        self.machine.get_execution_state(
            "MigrateMdsHandler"
        ).migrated_mds = migrated_mds

        if is_migration_required:
            self.logger.debug("Waiting for Rook based mds daemon '{0}'".format(mds_host))

            while True:
                result = self.ceph.mon_command("node ls")

                if mds_host in result["mds"]:
                    break

                sleep(2)

            self.logger.debug("Rook based mds daemon '{0}' available")

    @staticmethod
    def register_execution_state(
        machine: Machine, state_name: str, handler: ModuleHandler, **kwargs: Any
    ) -> None:
        ModuleHandler.register_execution_state(
            machine, state_name, handler, tags=["migrated_mds"]
        )
