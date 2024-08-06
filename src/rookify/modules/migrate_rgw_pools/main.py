# -*- coding: utf-8 -*-

from typing import Any, Dict
from ..exception import ModuleException
from ..machine import Machine
from ..module import ModuleHandler


class MigrateRgwPoolsHandler(ModuleHandler):
    REQUIRES = ["analyze_ceph", "migrate_mons"]

    def preflight(self) -> None:
        state_data = self.machine.get_preflight_state("AnalyzeCephHandler").data

        zones = self.machine.get_preflight_state_data(
            "MigrateRgwPoolsHandler", "zones", default_value={}
        )

        service_data = self.ceph.mon_command("service dump")

        rgw_daemons = service_data["services"].get("rgw", {}).get("daemons", {})  # type: ignore

        for rgw_daemon in rgw_daemons.values():
            if not isinstance(rgw_daemon, dict):
                continue

            zone_name = rgw_daemon["metadata"]["zone_name"]

            if zone_name not in zones:
                zones[zone_name] = {}

        osd_pools = self.ceph.get_osd_pool_configurations_from_osd_dump(
            state_data["osd"]["dump"]
        )

        for zone_name in zones:
            zone = zones[zone_name]

            for osd_pool_name, osd_pool_configuration in osd_pools.items():
                if osd_pool_name.startswith("{0}.rgw.".format(zone_name)):
                    zone[osd_pool_name] = osd_pool_configuration

            metadata_name = "{0}.rgw.meta".format(zone_name)

            if (
                metadata_name not in zone
                or "{0}.rgw.buckets.data".format(zone_name) not in zone
            ):
                raise ModuleException(
                    "Failed to identify required pools for RGW zone '{0}'".format(
                        zone_name
                    )
                )

            if zone[metadata_name].get("erasure_code_profile", "") != "":
                raise ModuleException(
                    "Ceph RGW metadata OSD pools must use replication for Rook"
                )

        self.machine.get_preflight_state("MigrateRgwPoolsHandler").zones = zones

    def execute(self) -> None:
        zones = self.machine.get_preflight_state("MigrateRgwPoolsHandler").zones

        for zone_name, zone_osd_pools_configuration in zones.items():
            self._migrate_zone(zone_name, zone_osd_pools_configuration)

    def _migrate_zone(
        self, zone_name: str, zone_osd_pools_configuration: Dict[str, Any]
    ) -> None:
        migrated_zones = self.machine.get_execution_state_data(
            "MigrateRgwPoolsHandler", "migrated_zones", default_value=[]
        )
        if zone_name in migrated_zones:
            return

        migrated_pools = self.machine.get_execution_state_data(
            "MigrateRgwPoolsHandler", "migrated_pools", default_value=[]
        )

        self.logger.debug("Migrating Ceph RGW zone '{0}'".format(zone_name))

        pool_metadata_osd_configuration = zone_osd_pools_configuration[
            "{0}.rgw.meta".format(zone_name)
        ]

        pool_data_osd_configuration = zone_osd_pools_configuration[
            "{0}.rgw.buckets.data".format(zone_name)
        ]

        pool_definition_values = {
            "cluster_namespace": self._config["rook"]["cluster"]["namespace"],
            "name": zone_name,
            "metadata_size": pool_metadata_osd_configuration["size"],
            "data_pool_size": pool_data_osd_configuration["size"],
            "rgw_placement_label": self.k8s.rgw_placement_label,
        }

        if pool_data_osd_configuration.get("erasure_code_profile", "") != "":
            profile_configuration = pool_data_osd_configuration[
                "erasure_code_configuration"
            ]

            pool_definition_values["data_erasure_code_configuration"] = {
                "coding": profile_configuration["m"],
                "data": profile_configuration["k"],
            }

        # Render cluster config from template
        pool_definition = self.load_template("pool.yaml.j2", **pool_definition_values)

        self.k8s.crd_api_apply(pool_definition.yaml)

        migrated_zones.append(zone_name)

        self.machine.get_execution_state(
            "MigrateRgwPoolsHandler"
        ).migrated_zones = migrated_zones

        for zone_osd_pool_name in zone_osd_pools_configuration:
            if zone_osd_pool_name not in migrated_pools:
                migrated_pools.append(zone_osd_pool_name)

        self.machine.get_execution_state(
            "MigrateRgwPoolsHandler"
        ).migrated_pools = migrated_pools

        self.logger.info("Migrated Ceph RGW zone '{0}'".format(zone_name))

    @staticmethod
    def register_execution_state(
        machine: Machine, state_name: str, handler: ModuleHandler, **kwargs: Any
    ) -> None:
        ModuleHandler.register_execution_state(
            machine, state_name, handler, tags=["migrated_pools", "migrated_zones"]
        )

    @staticmethod
    def register_preflight_state(
        machine: Machine, state_name: str, handler: ModuleHandler, **kwargs: Any
    ) -> None:
        ModuleHandler.register_preflight_state(
            machine, state_name, handler, tags=["zones"]
        )
