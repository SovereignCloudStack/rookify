# -*- coding: utf-8 -*-

from typing import Any
from ..exception import ModuleException
from ..machine import Machine
from ..module import ModuleHandler


class CreateRookClusterHandler(ModuleHandler):
    REQUIRES = [
        "analyze_ceph",
        "cephx_auth_config",
        "k8s_prerequisites_check",
        "create_rook_resources",
    ]

    def preflight(self) -> None:
        if self.machine.get_execution_state_data(
            "CreateRookClusterHandler", "generated", default_value=False
        ):
            return

        state_data = self.machine.get_preflight_state("AnalyzeCephHandler").data

        try:
            node_ls_data = state_data["node"]["ls"]
            rook_config = self._config["rook"]

            # Get monitor count
            mon_count = 0

            for node, mons in node_ls_data["mon"].items():
                if len(mons) > 1:
                    raise ModuleException(
                        f"There are more than 1 mon running on node {node}"
                    )

                mon_count += 1

            # Maximum number of mgr daemons currently supported by Rook (1.14), provide custom override
            if mon_count > 9:
                mon_count = rook_config["cluster"].get("max_mon_count", 9)

            # Get manager count
            mgr_count = 0

            for node, mgrs in node_ls_data["mgr"].items():
                if len(mons) > 1:
                    raise ModuleException(
                        f"There are more than 1 mgr running on node {node}"
                    )

                mgr_count += 1

            self.logger.debug(
                "Rook cluster definition values: {0} {1}".format(
                    rook_config["cluster"]["namespace"],
                    rook_config["cluster"]["name"],
                )
            )

            # Maximum number of mgr daemons currently supported by Rook (1.14), provide custom override
            if mgr_count > 5:
                mgr_count = rook_config["cluster"].get("max_mgr_count", 5)

            self.machine.get_execution_state(
                "CreateRookClusterHandler"
            ).mgr_count = mgr_count

            self.machine.get_execution_state(
                "CreateRookClusterHandler"
            ).mon_count = mon_count

            cluster_definition_values = {
                "cluster_name": rook_config["cluster"]["name"],
                "cluster_namespace": rook_config["cluster"]["namespace"],
                "ceph_image": rook_config["ceph"]["image"],
                "mon_count": mon_count,
                "mgr_count": mgr_count,
                "mgr_placement_label": self.k8s.mgr_placement_label,
                "mon_placement_label": self.k8s.mon_placement_label,
                "osd_placement_label": self.k8s.osd_placement_label,
            }

            if len(rook_config["ceph"].get("public_network", "")) > 0:
                cluster_definition_values["public_network"] = rook_config["ceph"][
                    "public_network"
                ]
            else:
                self.logger.warn(
                    "Rook Ceph cluster will be configured without a public network and determine it automatically during runtime"
                )

            if len(rook_config["ceph"].get("cluster_network", "")) > 0:
                cluster_definition_values["cluster_network"] = rook_config["ceph"][
                    "cluster_network"
                ]
            else:
                self.logger.info(
                    "Rook Ceph cluster will be configured without a cluster network"
                )

            # Render cluster config from template
            cluster_definition = self.load_template(
                "cluster.yaml.j2", **cluster_definition_values
            )

            self.machine.get_preflight_state(
                "CreateRookClusterHandler"
            ).cluster_definition = cluster_definition.yaml
        except KeyError:
            raise ModuleException("Ceph monitor data is incomplete")

    def execute(self) -> None:
        if self.machine.get_execution_state_data(
            "CreateRookClusterHandler", "generated", default_value=False
        ):
            return

        self.logger.info("Creating Rook cluster definition")

        # Create CephCluster
        cluster_definition = self.machine.get_preflight_state(
            "CreateRookClusterHandler"
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

        self.machine.get_execution_state("CreateRookClusterHandler").generated = True

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
    def register_execution_state(
        machine: Machine, state_name: str, handler: ModuleHandler, **kwargs: Any
    ) -> None:
        ModuleHandler.register_execution_state(
            machine, state_name, handler, tags=["generated"]
        )

    @staticmethod
    def register_preflight_state(
        machine: Machine, state_name: str, handler: ModuleHandler, **kwargs: Any
    ) -> None:
        ModuleHandler.register_preflight_state(
            machine,
            state_name,
            handler,
            tags=["cluster_definition", "mgr_count", "mon_count"],
        )
