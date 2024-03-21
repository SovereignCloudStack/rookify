# -*- coding: utf-8 -*-

from ..module import ModuleHandler, ModuleException

from typing import Any

import kubernetes


class CreateClusterHandler(ModuleHandler):
    def __create_cluster_definition(self) -> Any:
        try:
            node_ls_data = self._data["analyze_ceph"]["node"]["ls"]

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
            self.__cluster_name = self._config["rook"]["cluster"]["name"]
            self.__cluster_namespace = self._config["rook"]["cluster"]["namespace"]
            self.__cluster_image = self._config["rook"]["ceph"]["image"]
            self.__mon_placement_label = (
                self._config["rook"]["cluster"]["mon_placement_label"]
                if "mon_placement_label" in self._config["rook"]["cluster"]
                else f"placement-{self.__cluster_name}-mon"
            )
            self.__mgr_placement_label = (
                self._config["rook"]["cluster"]["mgr_placement_label"]
                if "mgr_placement_label" in self._config["rook"]["cluster"]
                else f"placement-{self.__cluster_name}-mgr"
            )
            self.__cluster_definition = self.load_template(
                "cluster.yaml.j2",
                cluster_name=self.__cluster_name,
                cluster_namespace=self.__cluster_namespace,
                ceph_image=self.__cluster_image,
                mon_count=mon_count,
                mgr_count=mgr_count,
                mon_placement_label=self.__mon_placement_label,
                mgr_placement_label=self.__mgr_placement_label,
            )

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

        # We have to check if our namespace exists
        namespace_exists = False
        namespaces = self.k8s.core_v1_api.list_namespace().items
        for namespace in namespaces:
            if namespace.metadata.name == self.__cluster_namespace:
                namespace_exists = True
        if not namespace_exists:
            raise ModuleException(
                f"Namespace {self.__cluster_namespace} does not exist"
            )

    def preflight(self) -> None:
        self.__create_cluster_definition()
        self.__check_k8s_prerequisites()

    def run(self) -> Any:
        # Create CephCluster
        self.k8s.crd_api_apply(self.__cluster_definition.yaml)

        # Wait for CephCluster to get into Progressing phase
        watcher = kubernetes.watch.Watch()
        stream = watcher.stream(
            self.k8s.custom_objects_api.list_namespaced_custom_object,
            "ceph.rook.io",
            "v1",
            self.__cluster_namespace,
            "cephclusters",
            timeout_seconds=60,
        )
        for event in stream:
            event_object = event["object"]

            if event_object["metadata"]["name"] != self.__cluster_name:
                continue

            try:
                if event_object["status"]["phase"] == "Progressing":
                    result = event_object
                    break
            except KeyError:
                pass
        watcher.stop()

        try:
            return result
        except NameError:
            raise ModuleException("CephCluster did not come up")
