# -*- coding: utf-8 -*-

from time import sleep
from typing import Any, Dict, List
from ..exception import ModuleException
from ..machine import Machine
from ..module import ModuleHandler


class MigrateRgwsHandler(ModuleHandler):
    REQUIRES = ["analyze_ceph", "migrate_rgw_pools"]

    def _get_rgw_daemon_hosts(self) -> List[str]:
        state_data = self.machine.get_preflight_state("AnalyzeCephHandler").data

        return self._get_rgw_daemon_hosts_of_map(
            state_data["report"]["servicemap"]["services"]
            .get("rgw", {})
            .get("daemons", {})
        )

    def _get_rgw_daemon_hosts_of_map(
        self, rgw_daemons_map: Dict[str, Any]
    ) -> List[str]:
        rgw_daemon_hosts = []

        if "summary" in rgw_daemons_map:
            del rgw_daemons_map["summary"]

        for rgw_daemon in rgw_daemons_map.values():
            if "metadata" not in rgw_daemon or "hostname" not in rgw_daemon["metadata"]:
                raise ModuleException(
                    "Unexpected ceph-rgw daemon metadata: {0}".format(rgw_daemon)
                )

            if rgw_daemon["metadata"]["hostname"] not in rgw_daemon_hosts:
                rgw_daemon_hosts.append(rgw_daemon["metadata"]["hostname"])

        return rgw_daemon_hosts

    def preflight(self) -> None:
        migrated_rgws = self.machine.get_execution_state_data(
            "MigrateRgwsHandler", "migrated_rgws", default_value=[]
        )

        if len(migrated_rgws) > 0:
            return

        self.k8s.check_nodes_for_initial_label_state(self.k8s.rgw_placement_label)

        rgw_daemon_hosts = self._get_rgw_daemon_hosts()

        for rgw_daemon_host in rgw_daemon_hosts:
            if rgw_daemon_host not in self._config["ssh"]["hosts"]:
                raise ModuleException(
                    "Unexpected ceph-rgw daemon found (no SSH config): {0}".format(
                        rgw_daemon_host
                    )
                )

    def execute(self) -> None:
        rgw_daemon_hosts = self._get_rgw_daemon_hosts()

        for rgw_daemon_host in rgw_daemon_hosts:
            self._migrate_rgw(rgw_daemon_host)

    def _migrate_rgw(self, rgw_host: str) -> None:
        migrated_rgws = self.machine.get_execution_state_data(
            "MigrateRgwsHandler", "migrated_rgws", default_value=[]
        )
        if rgw_host in migrated_rgws:
            return

        self.logger.info("Migrating ceph-rgw daemon at host '{0}'".format(rgw_host))

        migrated_zones = self.machine.get_execution_state_data(
            "MigrateRgwPoolsHandler", "migrated_zones", default_value=[]
        )
        is_migration_required = len(migrated_zones) > 0

        if is_migration_required:
            result = self.ssh.command(
                rgw_host,
                "sudo systemctl disable --now {0}".format(
                    self.ceph.get_systemd_rgw_file_name(rgw_host)
                ),
            )

            if result.failed:
                raise ModuleException(
                    "Disabling original ceph-rgw host {0} failed: {1}".format(
                        rgw_host, result.stderr
                    )
                )

            self.logger.debug(
                "Waiting for disabled original ceph-rgw host '{0}' to disconnect".format(
                    rgw_host
                )
            )

            while True:
                ceph_status = self.ceph.mon_command("status")

                rgw_daemon_hosts = self._get_rgw_daemon_hosts_of_map(
                    ceph_status["servicemap"]["services"]
                    .get("rgw", {})
                    .get("daemons", {})
                )

                if rgw_host not in rgw_daemon_hosts:
                    break

                sleep(2)

            self.logger.info("Disabled ceph-rgw host '{0}'".format(rgw_host))

        self.logger.debug("Enabling Rook based ceph-rgw node '{0}'".format(rgw_host))

        node_patch = {"metadata": {"labels": {self.k8s.rgw_placement_label: "true"}}}

        if (
            self.k8s.rgw_placement_label
            not in self.k8s.core_v1_api.patch_node(rgw_host, node_patch).metadata.labels
        ):
            raise ModuleException(
                "Failed to patch k8s node for ceph-rgw node '{0}'".format(rgw_host)
            )

        migrated_rgws.append(rgw_host)

        self.machine.get_execution_state(
            "MigrateRgwsHandler"
        ).migrated_rgws = migrated_rgws

        if is_migration_required:
            self.logger.debug(
                "Waiting for at least one Rook based RGW daemon for node '{0}'".format(
                    rgw_host
                )
            )

            while True:
                ceph_status = self.ceph.mon_command("status")

                rgw_daemon_hosts = self._get_rgw_daemon_hosts_of_map(
                    ceph_status["servicemap"]["services"]
                    .get("rgw", {})
                    .get("daemons", {})
                )

                if rgw_host in rgw_daemon_hosts:
                    break

                sleep(2)

            self.logger.info(
                "Rook based RGW daemon for node '{0}' available".format(rgw_host)
            )

    def get_readable_key_value_state(self) -> Dict[str, str]:
        return {
            "ceph RGW hosts": self._get_readable_json_dump(self._get_rgw_daemon_hosts())
        }

    @staticmethod
    def register_execution_state(
        machine: Machine, state_name: str, handler: ModuleHandler, **kwargs: Any
    ) -> None:
        ModuleHandler.register_execution_state(
            machine, state_name, handler, tags=["migrated_rgws"]
        )
