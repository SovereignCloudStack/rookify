# -*- coding: utf-8 -*-

import os
from os import path
from typing import Dict
from ..exception import ModuleException
from ..module import ModuleHandler


class OSISMConfigurationHandler(ModuleHandler):
    CONFIGURATION_FILE_NAME = "osism_configuration.yaml"
    IMAGES_FILE_NAME = "osism_images.yaml"

    REQUIRES = [
        "migrate_mons",
        "migrate_osds",
        "migrate_osd_pools",
        "migrate_mds",
        "migrate_mds_pools",
        "migrate_mgrs",
        "migrate_rgws",
        "migrate_rgw_pools",
    ]

    OSISM_CONFIGURATION_FILE_LOCATION = (
        "/opt/configuration/environments/rook/configuration.yml"
    )

    OSISM_IMAGES_FILE_LOCATION = "/opt/configuration/environments/rook/images.yml"
    OSISM_SECRETS_FILE_LOCATION = "/opt/configuration/environments/rook/secrets.yml"
    SECRETS_FILE_NAME = "osism_secrets.yaml"

    def preflight(self) -> None:
        if not os.access("./", os.W_OK):
            raise ModuleException(
                "OSISM configuration can not be written to the current working directory: {0}".format(
                    path.abspath("./")
                )
            )

    def execute(self) -> None:
        self._write_configuration_yaml()
        self._write_images_yaml()
        self._write_secrets_yaml()

    def get_readable_key_value_state(self) -> Dict[str, str]:
        return {"OSISM configuration path": path.abspath("./")}

    def _write_configuration_yaml(self) -> None:
        analyze_ceph_data = self.machine.get_preflight_state("AnalyzeCephHandler").data
        rook_config = self._config["rook"]

        (rook_ceph_repository, rook_ceph_version) = rook_config["ceph"]["image"].split(
            ":", 1
        )
        osd_hosts_list = [
            {"name": osd_host}
            for osd_host in analyze_ceph_data["node"]["ls"]["osd"].keys()
        ]

        create_rook_cluster_data = self.machine.get_preflight_state(
            "CreateRookClusterHandler"
        )

        configuration_values = {
            "ceph_repository": rook_ceph_repository,
            "ceph_version": rook_ceph_version,
            "cluster_name": rook_config["cluster"]["name"],
            "cluster_namespace": rook_config["cluster"]["namespace"],
            "osd_hosts_list": osd_hosts_list,
            "mon_count": create_rook_cluster_data.mon_count,
            "mgr_count": create_rook_cluster_data.mgr_count,
            "mds_count": len(analyze_ceph_data["node"]["ls"]["mds"]),
        }

        if len(rook_config["ceph"].get("public_network", "")) > 0:
            configuration_values["public_network"] = rook_config["ceph"][
                "public_network"
            ]

        if len(rook_config["ceph"].get("cluster_network", "")) > 0:
            configuration_values["cluster_network"] = rook_config["ceph"][
                "cluster_network"
            ]

        # Render cluster config from template
        configuration = self.load_template(
            "configuration.yaml.j2", **configuration_values
        )

        with open(OSISMConfigurationHandler.CONFIGURATION_FILE_NAME, "w") as fp:
            fp.write(configuration.raw)

        self.logger.info(
            "Generated '{0}' to be copied to '{1}'".format(
                OSISMConfigurationHandler.CONFIGURATION_FILE_NAME,
                OSISMConfigurationHandler.OSISM_CONFIGURATION_FILE_LOCATION,
            )
        )

    def _write_images_yaml(self) -> None:
        # Render cluster config from template
        images = self.load_template("images.yaml.j2")

        with open(OSISMConfigurationHandler.IMAGES_FILE_NAME, "w") as fp:
            fp.write(images.raw)

        self.logger.info(
            "Generated '{0}' to be copied to '{1}'".format(
                OSISMConfigurationHandler.IMAGES_FILE_NAME,
                OSISMConfigurationHandler.OSISM_IMAGES_FILE_LOCATION,
            )
        )

    def _write_secrets_yaml(self) -> None:
        # Render cluster config from template
        secrets = self.load_template("secrets.yaml.j2")

        with open(OSISMConfigurationHandler.SECRETS_FILE_NAME, "w") as fp:
            fp.write(secrets.raw)

        self.logger.info(
            "Generated '{0}' to be copied to '{1}'".format(
                OSISMConfigurationHandler.SECRETS_FILE_NAME,
                OSISMConfigurationHandler.OSISM_SECRETS_FILE_LOCATION,
            )
        )
