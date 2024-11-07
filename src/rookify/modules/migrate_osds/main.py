# -*- coding: utf-8 -*-

from collections import OrderedDict
from time import sleep
from typing import Any, Dict, List
from ..exception import ModuleException
from ..machine import Machine
from ..module import ModuleHandler


class MigrateOSDsHandler(ModuleHandler):
    REQUIRES = ["analyze_ceph", "migrate_mons"]

    def _get_devices_of_hosts(self) -> Dict[str, Dict[str, str]]:
        state_data = self.machine.get_preflight_state("AnalyzeCephHandler").data

        osd_devices: Dict[str, Dict[str, str]] = {}
        osd_metadata = {
            osd_data["id"]: osd_data
            for osd_data in state_data["report"]["osd_metadata"]
        }

        for osd_host, osds in state_data["node"]["ls"]["osd"].items():
            osd_devices[osd_host] = {}

            """
            Read OSD metadata to get OSD fsid UUID.
            From there we try to get the encrypted volume partition UUID for later use in Rook.
            """
            for osd_id in osds:
                if osd_id not in osd_metadata:
                    raise ModuleException(
                        "Found Ceph OSD ID {0} without metadata".format(osd_id)
                    )

                osd_data = osd_metadata[osd_id]

                result = self.ssh.command(
                    osd_host,
                    "sudo pvdisplay -c /dev/{0}".format(osd_data["devices"]),
                )

                if result.failed:
                    raise ModuleException("")

                osd_vg_name = result.stdout.split(":")[1]

                if osd_vg_name.startswith("ceph-"):
                    osd_vg_name = osd_vg_name[5:]

                osd_device_path = "/dev/ceph-{0}/osd-block-{0}".format(osd_vg_name)

                if osd_id not in osd_devices[osd_host]:
                    osd_devices[osd_host][osd_id] = osd_device_path

            self.logger.debug(
                "Analyzed {0:d} Ceph OSD(s) on host '{1}'".format(len(osds), osd_host)
            )

        return osd_devices

    def _get_nodes_osd_devices(self, osd_ids: List[str]) -> List[Dict[str, Any]]:
        osd_host_devices = self.machine.get_preflight_state(
            "MigrateOSDsHandler"
        ).osd_host_devices

        filtered_osd_host_devices: Dict[str, List[Dict[str, str]]] = {}

        for host, devices in osd_host_devices.items():
            for osd_id, device_path in devices.items():
                if osd_id in osd_ids:
                    if host not in filtered_osd_host_devices:
                        filtered_osd_host_devices[host] = []

                    filtered_osd_host_devices[host].append({"name": device_path})

        return [
            {"name": host, "devices": devices}
            for host, devices in filtered_osd_host_devices.items()
        ]

    def preflight(self) -> None:
        osd_host_devices = self.machine.get_preflight_state_data(
            "MigrateOSDsHandler", "osd_host_devices", default_value={}
        )

        if len(osd_host_devices) > 0:
            return

        self.k8s.check_nodes_for_initial_label_state(self.k8s.osd_placement_label)

        self.machine.get_preflight_state(
            "MigrateOSDsHandler"
        ).osd_host_devices = self._get_devices_of_hosts()

    def execute(self) -> None:
        osd_host_devices = self.machine.get_preflight_state_data(
            "MigrateOSDsHandler", "osd_host_devices", default_value={}
        )

        state_data = self.machine.get_preflight_state("AnalyzeCephHandler").data

        for host in osd_host_devices.keys():
            self.migrate_osds(host, state_data["node"]["ls"]["osd"][host])

    def get_readable_key_value_state(self) -> Dict[str, str]:
        state_data = self.machine.get_preflight_state("AnalyzeCephHandler").data

        osd_host_devices = self.machine.get_preflight_state_data(
            "MigrateOSDsHandler", "osd_host_devices", default_value={}
        )

        kv_state_data = OrderedDict()

        for host in state_data["node"]["ls"]["osd"].keys():
            if host in osd_host_devices:
                osd_device_list = []

                for osd_id, device_path in osd_host_devices[host].items():
                    osd_device_list.append(
                        {"OSD ID": osd_id, "Device path": device_path}
                    )

                kv_state_data["ceph OSD node {0} devices".format(host)] = (
                    self._get_readable_json_dump(osd_device_list)
                )
            else:
                kv_state_data["ceph OSD node {0} devices".format(host)] = (
                    "Not analyzed yet"
                )

        return kv_state_data

    def migrate_osds(self, host: str, osd_ids: List[int]) -> None:
        migrated_osd_ids = self.machine.get_execution_state_data(
            "MigrateOSDsHandler", "migrated_osd_ids", default_value=[]
        )

        self.logger.info("Migrating ceph-osd host '{0}'".format(host))

        node_patch = {"metadata": {"labels": {self.k8s.osd_placement_label: "true"}}}

        if (
            self.k8s.osd_placement_label
            not in self.k8s.core_v1_api.patch_node(host, node_patch).metadata.labels
        ):
            raise ModuleException(
                "Failed to patch k8s for ceph-osd node '{0}'".format(host)
            )

        for osd_id in osd_ids:
            if osd_id in migrated_osd_ids:
                return

            self.logger.debug(
                "Migrating ceph-osd daemon '{0}@{1:d}'".format(host, osd_id)
            )

            result = self.ssh.command(
                host,
                "sudo systemctl disable --now {0}".format(
                    self.ceph.get_systemd_osd_file_name(host, osd_id)
                ),
            )

            if result.failed:
                raise ModuleException(
                    "Disabling original ceph-osd daemon '{0}@{1:d}' failed: {2}".format(
                        host, osd_id, result.stderr
                    )
                )

            self.logger.debug(
                "Waiting for disabled original ceph-osd daemon '{0}@{1:d}' to disconnect".format(
                    host, osd_id
                )
            )

            while True:
                osd_status = self.ceph.mon_command("osd info", id=osd_id)

                if osd_status["up"] == 0:
                    break

                sleep(2)

            self.logger.info(
                "Disabled ceph-osd daemon '{0}@{1:d}'".format(host, osd_id)
            )

        self.logger.info("Enabling Rook based ceph-osd node '{0}'".format(host))

        nodes_osd_devices = self._get_nodes_osd_devices(migrated_osd_ids + osd_ids)

        cluster_patch_templated = self.load_template(
            "nodes_osd_devices_patch.yaml.j2",
            cluster_namespace=self._config["rook"]["cluster"]["namespace"],
            cluster_name=self._config["rook"]["cluster"]["name"],
            nodes_osd_devices_list=nodes_osd_devices,
        )

        crd_api = self.k8s.crd_api(api_version="ceph.rook.io/v1", kind="CephCluster")

        crd_api.patch(
            content_type="application/merge-patch+json",
            body=cluster_patch_templated.yaml,
        )

        for osd_id in osd_ids:
            migrated_osd_ids.append(osd_id)

        self.machine.get_execution_state(
            "MigrateOSDsHandler"
        ).migrated_osd_ids = migrated_osd_ids

        for osd_id in osd_ids:
            self.logger.debug(
                "Waiting for Rook based ceph-osd daemon '{0}@{1:d}'".format(
                    host, osd_id
                )
            )

            while True:
                osd_status = self.ceph.mon_command("osd info", id=osd_id)

                if osd_status["up"] != 0:
                    break

                sleep(2)

            self.logger.info(
                "Rook based ceph-osd daemon '{0}@{1:d}' available".format(host, osd_id)
            )

    @staticmethod
    def register_execution_state(
        machine: Machine, state_name: str, handler: ModuleHandler, **kwargs: Any
    ) -> None:
        ModuleHandler.register_execution_state(
            machine, state_name, handler, tags=["migrated_osd_ids"]
        )

    @staticmethod
    def register_preflight_state(
        machine: Machine, state_name: str, handler: ModuleHandler, **kwargs: Any
    ) -> None:
        ModuleHandler.register_preflight_state(
            machine, state_name, handler, tags=["osd_host_devices"]
        )
