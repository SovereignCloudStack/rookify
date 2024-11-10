# -*- coding: utf-8 -*-

from time import sleep
from typing import Any, Dict
from ..exception import ModuleException
from ..machine import Machine
from ..module import ModuleHandler


class MigrateMgrsHandler(ModuleHandler):
    REQUIRES = ["migrate_mons"]

    def preflight(self) -> None:
        migrated_mgrs = self.machine.get_execution_state_data(
            "MigrateMgrsHandler", "migrated_mgrs", default_value=[]
        )
        if len(migrated_mgrs) > 0:
            return

        self.k8s.check_nodes_for_initial_label_state(self.k8s.mgr_placement_label)

    def execute(self) -> None:
        state_data = self.machine.get_preflight_state("AnalyzeCephHandler").data

        for node in state_data["node"]["ls"]["mgr"].keys():
            self._migrate_mgr(node)

    def get_readable_key_value_state(self) -> Dict[str, str]:
        state_data = self.machine.get_preflight_state("AnalyzeCephHandler").data

        return {
            "ceph mgr daemons": self._get_readable_json_dump(
                list(state_data["node"]["ls"]["mgr"].keys())
            )
        }

    def _migrate_mgr(self, mgr_host: str) -> None:
        migrated_mgrs = self.machine.get_execution_state_data(
            "MigrateMgrsHandler", "migrated_mgrs", default_value=[]
        )
        if mgr_host in migrated_mgrs:
            return

        self.logger.info("Migrating ceph-mgr daemon at host'{0}'".format(mgr_host))

        result = self.ssh.command(
            mgr_host,
            "sudo systemctl disable --now {0}".format(
                self.ceph.get_systemd_mgr_file_name(mgr_host)
            ),
        )

        if result.failed:
            raise ModuleException(
                "Disabling original ceph-mgr daemon at host {0} failed: {1}".format(
                    mgr_host, result.stderr
                )
            )

        self.logger.debug(
            "Waiting for disabled original ceph-mgr daemon '{0}' to disconnect".format(
                mgr_host
            )
        )

        while True:
            result = self.ceph.mon_command("node ls")

            if mgr_host not in result["mgr"]:
                break

            sleep(2)

        self.logger.info(
            "Disabled ceph-mgr daemon '{0}' and enabling Rook based daemon".format(
                mgr_host
            )
        )

        node_patch = {"metadata": {"labels": {self.k8s.mgr_placement_label: "true"}}}

        if (
            self.k8s.mgr_placement_label
            not in self.k8s.core_v1_api.patch_node(mgr_host, node_patch).metadata.labels
        ):
            raise ModuleException(
                "Failed to patch k8s for ceph-mgr daemon node '{0}'".format(mgr_host)
            )

        migrated_mgrs.append(mgr_host)

        self.machine.get_execution_state(
            "MigrateMgrsHandler"
        ).migrated_mgrs = migrated_mgrs

        mgr_count_expected = self.machine.get_preflight_state_data(
            "CreateRookClusterHandler", "mgr_count", default_value=3
        )

        self.logger.debug(
            "Waiting for {0:d} ceph-mgr daemons to be available".format(
                mgr_count_expected
            )
        )

        while True:
            result = self.ceph.mon_command("node ls")
            if len(result["mgr"]) >= mgr_count_expected:
                break

            sleep(2)

        self.logger.info(
            "{0:d} ceph-mgr daemons are available".format(mgr_count_expected)
        )

    @staticmethod
    def register_execution_state(
        machine: Machine, state_name: str, handler: ModuleHandler, **kwargs: Any
    ) -> None:
        ModuleHandler.register_execution_state(
            machine, state_name, handler, tags=["migrated_mgrs"]
        )
