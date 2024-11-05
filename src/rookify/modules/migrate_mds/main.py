# -*- coding: utf-8 -*-

from time import sleep
from typing import Any, Dict
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

        for mds_host, mds_daemons in state_data["node"]["ls"]["mds"].items():
            if len(mds_daemons) > 1:
                raise ModuleException(
                    "There are more than 1 ceph-mds daemons running on host {0}".format(
                        mds_host
                    )
                )

    def execute(self) -> None:
        state_data = self.machine.get_preflight_state("AnalyzeCephHandler").data

        migrated_mds = self.machine.get_execution_state_data(
            "MigrateMdsHandler", "migrated_mds", default_value=[]
        )

        migrated_mds_pools = self.machine.get_execution_state_data(
            "MigrateMdsPoolsHandler", "migrated_mds_pools", default_value=[]
        )
        is_migration_required = len(migrated_mds_pools) > 0

        mds_hosts = list(state_data["node"]["ls"]["mds"].keys())

        # Rook may upgrade MDS and require all standby daemons to be inactive. Handle that while migration.
        has_mds_standby_daemons = len(mds_hosts) > 1

        for mds_host in mds_hosts:
            if mds_host in migrated_mds:
                continue

            self.logger.info("Migrating ceph-mds daemon at host '{0}'".format(mds_host))

            if (
                is_migration_required
                and has_mds_standby_daemons
                and mds_host not in (mds_hosts[0], mds_hosts[1])
            ):
                self._disable_mds(mds_host)

        for mds_host in mds_hosts:
            if mds_host in migrated_mds:
                continue

            if is_migration_required and (
                mds_host == mds_hosts[0]
                or (has_mds_standby_daemons and mds_host == mds_hosts[1])
            ):
                self._disable_mds(mds_host)

            self._set_mds_label(mds_host)

            migrated_mds.append(mds_host)

            self.machine.get_execution_state(
                "MigrateMdsHandler"
            ).migrated_mds = migrated_mds

            if is_migration_required:
                self._enable_rook_based_mds(mds_host)

    def _disable_mds(self, mds_host: str) -> None:
        result = self.ssh.command(
            mds_host,
            "sudo systemctl disable --now {0}".format(
                self.ceph.get_systemd_mds_file_name(mds_host)
            ),
        )

        if result.failed:
            raise ModuleException(
                "Disabling original ceph-mds daemon at host {0} failed: {1}".format(
                    mds_host, result.stderr
                )
            )

        self.logger.debug(
            "Waiting for disabled original ceph-mds daemon at host '{0}' to disconnect".format(
                mds_host
            )
        )

        while True:
            result = self.ceph.mon_command("node ls")

            if mds_host not in result["mds"]:
                break

            sleep(2)

        self.logger.info("Disabled ceph-mds daemon at host '{0}'".format(mds_host))

    def _set_mds_label(self, mds_host: str) -> None:
        node_patch = {"metadata": {"labels": {self.k8s.mds_placement_label: "true"}}}

        if (
            self.k8s.mds_placement_label
            not in self.k8s.core_v1_api.patch_node(mds_host, node_patch).metadata.labels
        ):
            raise ModuleException(
                "Failed to patch k8s for ceph-mds daemon node '{0}'".format(mds_host)
            )

    def _enable_rook_based_mds(self, mds_host: str) -> None:
        self.logger.debug(
            "Enabling and waiting for Rook based ceph-mds daemon node '{0}'".format(
                mds_host
            )
        )

        while True:
            result = self.ceph.mon_command("node ls")

            if mds_host in result["mds"]:
                break

            sleep(2)

        self.logger.info(
            "Rook based ceph-mds daemon node '{0}' available".format(mds_host)
        )

    def get_readable_key_value_state(self) -> Dict[str, str]:
        state_data = self.machine.get_preflight_state("AnalyzeCephHandler").data

        return {
            "ceph MDS daemons": self._get_readable_json_dump(
                list(state_data["node"]["ls"]["mds"].keys())
            )
        }

    @staticmethod
    def register_execution_state(
        machine: Machine, state_name: str, handler: ModuleHandler, **kwargs: Any
    ) -> None:
        ModuleHandler.register_execution_state(
            machine, state_name, handler, tags=["migrated_mds"]
        )
