# -*- coding: utf-8 -*-

import kubernetes
from ..machine import Machine
from ..module import ModuleHandler, ModuleException

from typing import Any, Dict


class CreateConfigMapHandler(ModuleHandler):
    REQUIRES = ["analyze_ceph", "k8s_prerequisites_check"]

    def __create_configmap_definition(self) -> None:
        state_data = self.machine.get_preflight_state("AnalyzeCephHandler").data

        metadata = kubernetes.client.V1ObjectMeta(name="rook-ceph-mon-endpoints")
        configmap_mon_list = ""

        for mon in state_data["mon"]["dump"]["mons"]:
            if configmap_mon_list != "":
                configmap_mon_list += ","

            configmap_mon_list += "{0}:{1}".format(
                mon["name"], mon["public_addr"].rsplit("/", 1)[0]
            )

        configmap_data = {
            "data": configmap_mon_list,
            "mapping": "{}",
            "maxMonId": "-1",
        }

        configmap = kubernetes.client.V1ConfigMap(
            api_version="v1", kind="ConfigMap", metadata=metadata, data=configmap_data
        )

        self.machine.get_preflight_state(
            "CreateConfigMapHandler"
        ).configmap = configmap.to_dict()

    def preflight(self) -> None:
        self.__cluster_name = self._config["rook"]["cluster"]["name"]

        state_data = self.machine.get_preflight_state("AnalyzeCephHandler").data
        self.__fsid = state_data["mon"]["dump"]["fsid"]

        # If the configmap or secret already exists, we have to abort to not override it
        try:
            self.k8s.core_v1_api.read_namespaced_config_map(
                "rook-ceph-mon-endpoints", self._config["rook"]["cluster"]["namespace"]
            )
        except kubernetes.client.exceptions.ApiException:
            pass
        else:
            raise ModuleException("Configmap rook-ceph-mon-endpoints already exists")

        # If the secret already exists, we have to abort to not override it
        try:
            self.k8s.core_v1_api.read_namespaced_secret(
                "rook-ceph-mon", self._config["rook"]["cluster"]["namespace"]
            )
        except kubernetes.client.exceptions.ApiException:
            pass
        else:
            raise ModuleException("Secret rook-ceph-mon already exists")

        self.__create_configmap_definition()

    def execute(self) -> None:
        configmap = kubernetes.client.V1ConfigMap(
            **self.machine.get_preflight_state("CreateConfigMapHandler").configmap
        )

        configmap = self.k8s.core_v1_api.create_namespaced_config_map(
            self._config["rook"]["cluster"]["namespace"], body=configmap
        )

        self.machine.get_execution_state(
            "CreateConfigMapHandler"
        ).configmap = configmap.to_dict()

        # Get or create needed auth keys
        admin_auth: Dict[str, Any] = self.ceph.mon_command(
            "auth get-or-create-key",
            entity="client.admin",
            mon="allow *",
            mgr="allow *",
            mds="allow *",
        )  # type: ignore

        mon_auth: Dict[str, Any] = self.ceph.mon_command(
            "auth get-or-create-key", entity="mon.", mon="allow *"
        )  # type: ignore

        metadata = kubernetes.client.V1ObjectMeta(name="rook-ceph-mon")

        string_data = {
            "admin-secret": admin_auth["key"],
            "cluster-name": self.__cluster_name,
            "fsid": self.__fsid,
            "mon-secret": mon_auth["key"],
        }

        secret = kubernetes.client.V1Secret(
            api_version="v1", kind="Secret", metadata=metadata, string_data=string_data
        )

        secret = self.k8s.core_v1_api.create_namespaced_secret(
            self._config["rook"]["cluster"]["namespace"], body=secret
        )

        self.machine.get_execution_state(
            "CreateConfigMapHandler"
        ).secret = secret.to_dict()

    @staticmethod
    def register_execution_state(
        machine: Machine, state_name: str, handler: ModuleHandler, **kwargs: Any
    ) -> None:
        ModuleHandler.register_execution_state(
            machine, state_name, handler, tags=["secret"]
        )

    @staticmethod
    def register_preflight_state(
        machine: Machine, state_name: str, handler: ModuleHandler, **kwargs: Any
    ) -> None:
        ModuleHandler.register_preflight_state(
            machine, state_name, handler, tags=["configmap"]
        )
