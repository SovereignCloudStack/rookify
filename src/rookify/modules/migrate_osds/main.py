# -*- coding: utf-8 -*-

from typing import Any, Dict, List
from ..exception import ModuleException
from ..machine import Machine
from ..module import ModuleHandler


class MigrateOSDsHandler(ModuleHandler):
    REQUIRES = ["migrate_mons"]

    def _get_devices_of_hosts(self) -> Dict[str, List[str]]:
        state_data = self.machine.get_preflight_state("AnalyzeCephHandler").data
        osd_devices: Dict[str, List[str]] = {}

        for osd_host, osds in state_data["node"]["ls"]["osd"].items():
            osd_devices[osd_host] = []

            """
            Read OSD metadata to get OSD fsid UUID.
            From there we try to get the encrypted volume partition UUID for later use in Rook.
            """
            for osd_id in osds:
                osd_data = self.ceph.mon_command("osd metadata", id=osd_id)

                result = self.ssh.command(
                    osd_host,
                    "sudo pvdisplay -c /dev/{0}".format(osd_data["devices"]),  # type:ignore
                )

                if result.failed:
                    raise ModuleException("")

                osd_vg_name = result.stdout.split(":")[1]

                if osd_vg_name.startswith("ceph-"):
                    osd_vg_name = osd_vg_name[5:]

                osd_device_path = "/dev/ceph-{0}/osd-block-{0}".format(osd_vg_name)

                if osd_device_path not in osd_devices[osd_host]:
                    osd_devices[osd_host].append(osd_device_path)

        return osd_devices

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
        if self.machine.get_execution_state_data(
            "MigrateOSDsHandler", "migrated", default_value=False
        ):
            return

        osd_host_devices = self.machine.get_preflight_state(
            "MigrateOSDsHandler"
        ).osd_host_devices

        nodes_osd_devices = [
            {"name": host, "devices": [{"name": device} for device in devices]}
            for host, devices in osd_host_devices.items()
        ]

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

        for host in osd_host_devices:
            node_patch = {
                "metadata": {"labels": {self.k8s.mon_placement_label: "true"}}
            }

            if (
                self.k8s.mon_placement_label
                not in self.k8s.core_v1_api.patch_node(host, node_patch).metadata.labels
            ):
                raise ModuleException(
                    "Failed to patch k8s node for Ceph mon daemon '{0}'".format(host)
                )

        self.machine.get_execution_state("MigrateOSDsHandler").migrated = True

    @staticmethod
    def register_execution_state(
        machine: Machine, state_name: str, handler: ModuleHandler, **kwargs: Any
    ) -> None:
        ModuleHandler.register_execution_state(
            machine, state_name, handler, tags=["migrated"]
        )

    @staticmethod
    def register_preflight_state(
        machine: Machine, state_name: str, handler: ModuleHandler, **kwargs: Any
    ) -> None:
        ModuleHandler.register_preflight_state(
            machine, state_name, handler, tags=["osd_host_devices"]
        )
