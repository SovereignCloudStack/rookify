# -*- coding: utf-8 -*-

from collections import OrderedDict
from typing import Any, Dict
from ..machine import Machine
from ..module import ModuleHandler


class MigrateMdsPoolsHandler(ModuleHandler):
    REQUIRES = ["analyze_ceph", "migrate_mons"]

    def preflight(self) -> None:
        state_data = self.machine.get_preflight_state("AnalyzeCephHandler").data

        pools = self.machine.get_preflight_state_data(
            "MigrateMdsPoolsHandler", "pools", default_value={}
        )

        osd_pools = self.ceph.get_osd_pool_configurations_from_map(
            state_data["report"]["osdmap"]
        )

        for mds_fs_data in state_data["fs"]["ls"]:
            if not mds_fs_data["metadata_pool"].endswith("-metadata"):
                self.logger.warn(
                    "ceph-mds filesystem '{0}' uses an incompatible pool metadata name '{1}' and can not be migrated to Rook automatically".format(
                        mds_fs_data["name"], mds_fs_data["metadata_pool"]
                    )
                )

                # Store pools for incompatible MDS filesystem as migrated ones
                migrated_pools = self.machine.get_execution_state_data(
                    "MigrateMdsPoolsHandler", "migrated_pools", default_value=[]
                )

                if mds_fs_data["metadata_pool"] not in migrated_pools:
                    migrated_pools.append(mds_fs_data["metadata_pool"])

                for pool_data_osd_name in mds_fs_data["data_pools"]:
                    if pool_data_osd_name not in migrated_pools:
                        migrated_pools.append(pool_data_osd_name)

                state = self.machine.get_execution_state("MigrateMdsPoolsHandler")
                if state is not None:
                    state.migrated_pools = migrated_pools

                continue

            pool = {
                "name": mds_fs_data["name"],
                "metadata": mds_fs_data["metadata_pool"],
                "data": [pool for pool in mds_fs_data["data_pools"]],
                "osd_pool_configurations": {},
            }

            pool["osd_pool_configurations"][mds_fs_data["metadata_pool"]] = osd_pools[
                mds_fs_data["metadata_pool"]
            ]

            for mds_ods_pool_name in mds_fs_data["data_pools"]:
                pool["osd_pool_configurations"][mds_ods_pool_name] = osd_pools[
                    mds_ods_pool_name
                ]

            pools[mds_fs_data["name"]] = pool

        self.machine.get_preflight_state("MigrateMdsPoolsHandler").pools = pools

    def execute(self) -> None:
        pools = self.machine.get_preflight_state("MigrateMdsPoolsHandler").pools

        for pool in pools.values():
            self._migrate_pool(pool)

    def get_readable_key_value_state(self) -> Dict[str, str]:
        migrated_mds_pools = self.machine.get_execution_state_data(
            "MigrateMdsPoolsHandler", "migrated_mds_pools", default_value=[]
        )

        pools = self.machine.get_preflight_state_data(
            "MigrateMdsPoolsHandler", "pools", default_value={}
        )

        kv_state_data = OrderedDict()

        for pool in pools:
            key_name = "ceph MDS pool {0}".format(pool["name"])
            kv_state_data[key_name] = self._get_readable_json_dump(pool)

            key_name = "ceph MDS pool {0} is created".format(pool["name"])
            kv_state_data[key_name] = pool["name"] in migrated_mds_pools

        return kv_state_data

    def _migrate_pool(self, pool: Dict[str, Any]) -> None:
        migrated_mds_pools = self.machine.get_execution_state_data(
            "MigrateMdsPoolsHandler", "migrated_mds_pools", default_value=[]
        )
        if pool["name"] in migrated_mds_pools:
            return

        migrated_pools = self.machine.get_execution_state_data(
            "MigrateMdsPoolsHandler", "migrated_pools", default_value=[]
        )

        state_data = self.machine.get_preflight_state("AnalyzeCephHandler").data

        self.logger.info("Migrating ceph-mds pool '{0}'".format(pool["name"]))
        osd_pool_configurations = pool["osd_pool_configurations"]

        pool_metadata_osd_configuration = osd_pool_configurations[pool["metadata"]]

        filesystem_definition_values = {
            "cluster_namespace": self._config["rook"]["cluster"]["namespace"],
            "name": pool["name"],
            "mds_instances": len(state_data["node"]["ls"]["mds"]),
            "mds_size": pool_metadata_osd_configuration["size"],
            "mds_placement_label": self.k8s.mds_placement_label,
        }

        filesystem_definition_values["data_pools"] = []

        for pool_data_osd_name in pool["data"]:
            osd_configuration = osd_pool_configurations[pool_data_osd_name]

            definition_data_pool = {
                "name": osd_configuration["pool_name"],
                "size": osd_configuration["size"],
            }

            if osd_configuration.get("erasure_code_profile", "") != "":
                profile_configuration = osd_configuration["erasure_code_configuration"]

                definition_data_pool["erasure_code_configuration"] = {
                    "coding": profile_configuration["m"],
                    "data": profile_configuration["k"],
                }

            filesystem_definition_values["data_pools"].append(definition_data_pool)

        # Render cluster config from template
        pool_definition = self.load_template(
            "filesystem.yaml.j2", **filesystem_definition_values
        )

        self.k8s.crd_api_apply(pool_definition.yaml)

        if pool["name"] not in migrated_mds_pools:
            migrated_mds_pools.append(pool["name"])

        self.machine.get_execution_state(
            "MigrateMdsPoolsHandler"
        ).migrated_mds_pools = migrated_mds_pools

        if pool["metadata"] not in migrated_pools:
            migrated_pools.append(pool["metadata"])

        for pool_data_osd_name in pool["data"]:
            if pool_data_osd_name not in migrated_pools:
                migrated_pools.append(pool_data_osd_name)

        self.machine.get_execution_state(
            "MigrateMdsPoolsHandler"
        ).migrated_pools = migrated_pools

        self.logger.info("Migrated ceph-mds pool '{0}'".format(pool["name"]))

    @staticmethod
    def register_execution_state(
        machine: Machine, state_name: str, handler: ModuleHandler, **kwargs: Any
    ) -> None:
        ModuleHandler.register_execution_state(
            machine, state_name, handler, tags=["migrated_pools", "migrated_mds_pools"]
        )

    @staticmethod
    def register_preflight_state(
        machine: Machine, state_name: str, handler: ModuleHandler, **kwargs: Any
    ) -> None:
        ModuleHandler.register_preflight_state(
            machine, state_name, handler, tags=["pools"]
        )
