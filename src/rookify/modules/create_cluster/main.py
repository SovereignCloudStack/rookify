# -*- coding: utf-8 -*-

import kubernetes
from typing import Any
from ..machine import Machine
from ..module import ModuleHandler, ModuleException


class CreateClusterHandler(ModuleHandler):
    REQUIRES = [
        "analyze_ceph",
        "cephx_auth_config",
        "k8s_prerequisites_check",
        "create_configmap",
    ]

    @property
    def __mon_placement_label(self) -> str:
        return (
            self._config["rook"]["cluster"]["mon_placement_label"]
            if "mon_placement_label" in self._config["rook"]["cluster"]
            else f"placement-{self._config["rook"]["cluster"]["name"]}-mon"
        )

    @property
    def __mgr_placement_label(self) -> str:
        return (
            self._config["rook"]["cluster"]["mgr_placement_label"]
            if "mgr_placement_label" in self._config["rook"]["cluster"]
            else f"placement-{self._config["rook"]["cluster"]["name"]}-mgr"
        )

    def __create_cluster_definition(self) -> None:
        state_data = self.machine.get_preflight_state("AnalyzeCephHandler").data

        try:
            node_ls_data = state_data["node"]["ls"]

            # Get monitor count
            mon_count = 0
            for node, mons in node_ls_data["mon"].items():
                mon_count += 1
                if len(mons) > 1:
                    raise ModuleException(
                        f"There are more than 1 mon running on node {node}"
                    )

            # Get manager count
            mgr_count = 0
            for node, mgrs in node_ls_data["mgr"].items():
                mgr_count += 1
                if len(mons) > 1:
                    raise ModuleException(
                        f"There are more than 1 mgr running on node {node}"
                    )

            # Render cluster config from template
            cluster_definition = self.load_template(
                "cluster.yaml.j2",
                cluster_name=self._config["rook"]["cluster"]["name"],
                cluster_namespace=self._config["rook"]["cluster"]["namespace"],
                ceph_image=self._config["rook"]["ceph"]["image"],
                mon_count=mon_count,
                mgr_count=mgr_count,
                mon_placement_label=self.__mon_placement_label,
                mgr_placement_label=self.__mgr_placement_label,
            )

            self.machine.get_preflight_state(
                "CreateClusterHandler"
            ).cluster_definition = cluster_definition.yaml
        except KeyError:
            raise ModuleException("Ceph monitor data is incomplete")

    def __check_k8s_prerequisites(self) -> None:
        # We have to check, if our placement labels are disabled or unset
        nodes = self.k8s.core_v1_api.list_node().items
        for node in nodes:
            node_labels = node.metadata.labels
            if (
                self.__mon_placement_label in node_labels
                and node_labels[self.__mon_placement_label] == "enabled"
            ):
                raise ModuleException(
                    f"Label {self.__mon_placement_label} is set on node {node.metadata.name}"
                )
            if (
                self.__mgr_placement_label in node_labels
                and node_labels[self.__mgr_placement_label] == "enabled"
            ):
                raise ModuleException(
                    f"Label {self.__mon_placement_label} is set on node {node.metadata.name}"
                )

    def preflight(self) -> None:
        self.__check_k8s_prerequisites()
        self.__create_cluster_definition()

    def execute(self) -> None:
        # Create CephCluster
        cluster_definition = self.machine.get_preflight_state(
            "CreateClusterHandler"
        ).cluster_definition

        self.k8s.crd_api_apply(cluster_definition)

        cluster_name = self._config["rook"]["cluster"]["name"]

        # Wait for CephCluster to get into Progressing phase
        result = None
        watcher = kubernetes.watch.Watch()

        stream = watcher.stream(
            self.k8s.custom_objects_api.list_namespaced_custom_object,
            "ceph.rook.io",
            "v1",
            self._config["rook"]["cluster"]["namespace"],
            "cephclusters",
            timeout_seconds=60,
        )

        for event in stream:
            event_object = event["object"]

            if event_object["metadata"]["name"] != cluster_name:
                continue

            try:
                if event_object["status"]["phase"] == "Progressing":
                    result = event_object
                    break
            except KeyError:
                pass

        watcher.stop()

        if result == None:
            raise ModuleException("CephCluster did not come up")

    @staticmethod
    def register_preflight_state(
        machine: Machine, state_name: str, handler: ModuleHandler, **kwargs: Any
    ) -> None:
        ModuleHandler.register_preflight_state(
            machine, state_name, handler, tags=["cluster_definition"]
        )
