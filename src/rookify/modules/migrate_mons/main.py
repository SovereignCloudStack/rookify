# -*- coding: utf-8 -*-

from time import sleep
from typing import Any, Dict
from ..exception import ModuleException
from ..machine import Machine
from ..module import ModuleHandler


class MigrateMonsHandler(ModuleHandler):
    REQUIRES = ["analyze_ceph", "create_rook_cluster"]

    def preflight(self) -> None:
        migrated_mons = self.machine.get_execution_state_data(
            "MigrateMonsHandler", "migrated_mons", default_value=[]
        )
        if len(migrated_mons) > 0:
            return

        self.k8s.check_nodes_for_initial_label_state(self.k8s.mon_placement_label)

    def execute(self) -> None:
        state_data = self.machine.get_preflight_state("AnalyzeCephHandler").data

        for mon in state_data["mon"]["dump"]["mons"]:
            self._migrate_mon(mon)

    def _migrate_mon(self, mon: Dict[str, Any]) -> None:
        migrated_mons = self.machine.get_execution_state_data(
            "MigrateMonsHandler", "migrated_mons", default_value=[]
        )
        if mon["name"] in migrated_mons:
            return

        self.logger.debug("Migrating Ceph mon daemon '{0}'".format(mon["name"]))

        result = self.ssh.command(
            mon["name"], "sudo systemctl disable --now ceph-mon.target"
        )

        if result.failed:
            raise ModuleException(
                "Disabling original Ceph mon daemon at host {0} failed: {1}".format(
                    mon["name"], result.stderr
                )
            )

        self.logger.debug(
            "Waiting for disabled original Ceph mon daemon '{0}' to disconnect".format(
                mon["name"]
            )
        )

        while True:
            result = self.ceph.mon_command("mon stat")
            quorum_names = [
                quorum_details["name"] for quorum_details in result["quorum"]
            ]

            if mon["name"] not in quorum_names:
                break

            sleep(2)

        self.logger.info("Disabled Ceph mon daemon '{0}'".format(mon["name"]))

        self.ceph.mon_command("mon remove", name=mon["name"])

        self.logger.info(
            "Enabling Rook based Ceph mon daemon '{0}'".format(mon["name"])
        )

        node_patch = {"metadata": {"labels": {self.k8s.mon_placement_label: "true"}}}

        if (
            self.k8s.mon_placement_label
            not in self.k8s.core_v1_api.patch_node(
                mon["name"], node_patch
            ).metadata.labels
        ):
            raise ModuleException(
                "Failed to patch k8s node for Ceph mon daemon '{0}'".format(mon["name"])
            )

        migrated_mons += mon["name"]

        self.machine.get_execution_state(
            "MigrateMonsHandler",
        ).migrated_mons = migrated_mons

        mon_count_expected = self.machine.get_execution_state(
            "CreateRookClusterHandler"
        ).mon_count

        self.logger.debug(
            "Waiting for a quorum of {0:d} Ceph mon daemons".format(mon_count_expected)
        )

        while True:
            result = self.ceph.mon_command("mon stat")
            if len(result["quorum"]) >= mon_count_expected:
                break

            sleep(2)

        self.logger.debug(
            "Quorum of {0:d} Ceph mon daemons successful".format(mon_count_expected)
        )

    @staticmethod
    def register_execution_state(
        machine: Machine, state_name: str, handler: ModuleHandler, **kwargs: Any
    ) -> None:
        ModuleHandler.register_execution_state(
            machine, state_name, handler, tags=["migrated_mons"]
        )
