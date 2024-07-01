# -*- coding: utf-8 -*-

from typing import Any, Dict
from ..machine import Machine
from ..module import ModuleHandler


class MigrateOSDPoolsHandler(ModuleHandler):
    REQUIRES = ["analyze_ceph", "migrate_mds_pools", "migrate_rgw_pools"]

    def execute(self) -> None:
        state_data = self.machine.get_preflight_state("AnalyzeCephHandler").data

        migrated_mds_pools = getattr(
            self.machine.get_execution_state("MigrateMdsPoolsHandler"),
            "migrated_pools",
            [],
        )

        migrated_rgw_pools = getattr(
            self.machine.get_execution_state("MigrateRgwPoolsHandler"),
            "migrated_pools",
            [],
        )

        migrated_pools = migrated_mds_pools + migrated_rgw_pools

        osd_pool_configurations = self.ceph.get_osd_pool_configurations_from_osd_dump(
            state_data["osd"]["dump"]
        )

        pools = []

        for pool in osd_pool_configurations.values():
            if (
                not pool["pool_name"].startswith(".")
                and pool["pool_name"] not in migrated_pools
            ):
                pools.append(pool)

        for pool in pools:
            self._migrate_pool(pool)

    def _migrate_pool(self, pool: Dict[str, Any]) -> None:
        migrated_pools = getattr(
            self.machine.get_execution_state("MigrateOSDPoolsHandler"),
            "migrated_pools",
            [],
        )

        if pool["pool_name"] in migrated_pools:
            return

        self.logger.debug("Migrating Ceph OSD pool '{0}'".format(pool["pool_name"]))

        pool_definition_values = {
            "cluster_namespace": self._config["rook"]["cluster"]["namespace"],
            "name": pool["pool_name"],
            "size": pool["size"],
        }

        # Render cluster config from template
        pool_definition = self.load_template("pool.yaml.j2", **pool_definition_values)

        self.k8s.crd_api_apply(pool_definition.yaml)
        migrated_pools.append(pool["pool_name"])

        self.logger.info("Migrated Ceph OSD pool '{0}'".format(pool["pool_name"]))

    @staticmethod
    def register_execution_state(
        machine: Machine, state_name: str, handler: ModuleHandler, **kwargs: Any
    ) -> None:
        ModuleHandler.register_execution_state(
            machine, state_name, handler, tags=["migrated_pools"]
        )
