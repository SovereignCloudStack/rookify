# -*- coding: utf-8 -*-

from typing import Any
from ..exception import ModuleException
from ..machine import Machine
from ..module import ModuleHandler


class CreateClusterHandler(ModuleHandler):
    REQUIRES = [
        "analyze_ceph",
        "cephx_auth_config",
        "k8s_prerequisites_check",
        "create_configmap",
    ]

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

            self.logger.debug(
                "Rook cluster definition values: {0} {1} with mon label {2} and mgr label {3}".format(
                    self._config["rook"]["cluster"]["namespace"],
                    self._config["rook"]["cluster"]["name"],
                    self.k8s.mon_placement_label,
                    self.k8s.mgr_placement_label,
                )
            )

            cluster_definition_values = {
                "cluster_name":self._config["rook"]["cluster"]["name"],
                "cluster_namespace":self._config["rook"]["cluster"]["namespace"],
                "ceph_image":self._config["rook"]["ceph"]["image"],
                "mon_count":mon_count,
                "mgr_count":mgr_count,
                "mon_placement_label":self.k8s.mon_placement_label,
                "mgr_placement_label":self.k8s.mgr_placement_label,
            }

            if len(self._config["rook"]["ceph"].get("public_network", "")) > 0:
                cluster_definition_values["public_network"] = self._config["rook"]["ceph"]["public_network"]
            else:
                self.logger.warn("Rook Ceph cluster will be configured without a public network and determine it automatically during runtime")

            if len(self._config["rook"]["ceph"].get("cluster_network", "")) > 0:
                cluster_definition_values["cluster_network"] = self._config["rook"]["ceph"]["cluster_network"]
            else:
                self.logger.info("Rook Ceph cluster will be configured without a cluster network")

            # Render cluster config from template
            cluster_definition = self.load_template(
                "cluster.yaml.j2",
                **cluster_definition_values
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
                self.k8s.mon_placement_label in node_labels
                and node_labels[self.k8s.mon_placement_label] == "enabled"
            ):
                raise ModuleException(
                    f"Label {self.k8s.mon_placement_label} is set on node {node.metadata.name}"
                )

            if (
                self.k8s.mgr_placement_label in node_labels
                and node_labels[self.k8s.mgr_placement_label] == "enabled"
            ):
                raise ModuleException(
                    f"Label {self.k8s.mon_placement_label} is set on node {node.metadata.name}"
                )

    def preflight(self) -> None:
        self.__check_k8s_prerequisites()
        self.__create_cluster_definition()

    def execute(self) -> None:
        self.logger.info("Creating Rook cluster definition")

        # Create CephCluster
        cluster_definition = self.machine.get_preflight_state(
            "CreateClusterHandler"
        ).cluster_definition

        self.k8s.crd_api_apply(cluster_definition)

        # Wait for CephCluster to get into Progressing phase
        self.logger.info("Waiting for Rook cluster created")

        result = self.k8s.watch_events(
            self._watch_cluster_phase_callback,
            self.k8s.custom_objects_api.list_namespaced_custom_object,
            "ceph.rook.io",
            "v1",
            self._config["rook"]["cluster"]["namespace"],
            "cephclusters",
            timeout_seconds=60,
        )

        if result is None:
            raise ModuleException("CephCluster did not come up")

    def _watch_cluster_phase_callback(self, event_object: Any) -> Any:
        try:
            if (
                event_object["metadata"]["name"]
                == self._config["rook"]["cluster"]["name"]
                and event_object["status"]["phase"] == "Progressing"
            ):
                return event_object
        except KeyError:
            pass

        return None

    @staticmethod
    def register_preflight_state(
        machine: Machine, state_name: str, handler: ModuleHandler, **kwargs: Any
    ) -> None:
        ModuleHandler.register_preflight_state(
            machine, state_name, handler, tags=["cluster_definition"]
        )
