# -*- coding: utf-8 -*-

import kubernetes
import json
from collections import OrderedDict
from typing import Any, Dict
from ..exception import ModuleException
from ..machine import Machine
from ..module import ModuleHandler


class CreateRookResourcesHandler(ModuleHandler):
    REQUIRES = ["analyze_ceph", "k8s_prerequisites_check"]

    def __create_configmap_definition(self) -> None:
        state_data = self.machine.get_preflight_state("AnalyzeCephHandler").data

        metadata = kubernetes.client.V1ObjectMeta(name="rook-ceph-mon-endpoints")
        configmap_mon_list = ""
        mapping = {}

        for mon in state_data["report"]["monmap"]["mons"]:
            if configmap_mon_list != "":
                configmap_mon_list += ","

            configmap_mon_list += "{0}={1}".format(
                mon["name"], mon["public_addr"].rsplit("/", 1)[0]
            )

            mapping[mon["name"]] = {
                "Name": mon["name"],
                "Hostname": mon["name"],
                "Address": mon["public_addr"].rsplit(":", 1)[0],
            }

        configmap_data = {
            "data": configmap_mon_list,
            "mapping": json.dumps({"node": mapping}),
            "maxMonId": "{0:d}".format(len(state_data["report"]["monmap"]["mons"])),
        }

        configmap = kubernetes.client.V1ConfigMap(
            api_version="v1", kind="ConfigMap", metadata=metadata, data=configmap_data
        )

        self.machine.get_preflight_state(
            "CreateRookResourcesHandler"
        ).configmap = configmap.to_dict()

    def preflight(self) -> None:
        configmap = self.machine.get_preflight_state_data(
            "CreateRookResourcesHandler", "configmap", default_value={}
        )

        if len(configmap) > 0:
            return

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
        if (
            len(
                self.machine.get_execution_state_data(
                    "CreateRookResourcesHandler", "secret", default_value={}
                )
            )
            > 0
        ):
            return

        configmap = kubernetes.client.V1ConfigMap(
            **self.machine.get_preflight_state("CreateRookResourcesHandler").configmap
        )

        configmap_created = self.k8s.core_v1_api.create_namespaced_config_map(
            self._config["rook"]["cluster"]["namespace"], body=configmap
        )

        self.machine.get_execution_state(
            "CreateRookResourcesHandler"
        ).configmap = configmap_created.to_dict()

        # Get or create needed auth keys
        admin_auth: Dict[str, Any] = self.ceph.mon_command(
            "auth get-or-create-key",
            entity="client.admin",
            mon="allow *",
            mgr="allow *",
            mds="allow *",
        )

        mon_auth: Dict[str, Any] = self.ceph.mon_command(
            "auth get-or-create-key", entity="mon.", mon="allow *"
        )

        metadata = kubernetes.client.V1ObjectMeta(name="rook-ceph-mon")

        state_data = self.machine.get_preflight_state("AnalyzeCephHandler").data

        secret_data = {
            "admin-secret": admin_auth["key"],
            "cluster-name": self._config["rook"]["cluster"]["name"],
            "fsid": state_data["report"]["monmap"]["fsid"],
            "mon-secret": mon_auth["key"],
        }

        secret = kubernetes.client.V1Secret(
            api_version="v1", kind="Secret", metadata=metadata, string_data=secret_data
        )

        secret = self.k8s.core_v1_api.create_namespaced_secret(
            self._config["rook"]["cluster"]["namespace"], body=secret
        )

        self.machine.get_execution_state(
            "CreateRookResourcesHandler"
        ).secret = secret.to_dict()

    def get_readable_key_value_state(self) -> Dict[str, str]:
        kv_state_data = OrderedDict()

        configmap = self.machine.get_preflight_state_data(
            "CreateRookResourcesHandler", "configmap"
        )

        if configmap is None:
            kv_state_data["rook-ceph-mon-endpoints"] = "Not created yet"
        else:
            kv_state_data["rook-ceph-mon-endpoints"] = self._get_readable_json_dump(
                configmap
            )

        secret = self.machine.get_execution_state_data(
            "CreateRookResourcesHandler", "secret"
        )

        if secret is None:
            kv_state_data["rook-ceph-mon-endpoints has been created"] = "False"
            kv_state_data["rook-ceph-mon"] = "Not created yet"
        else:
            kv_state_data["rook-ceph-mon-endpoints has been created"] = "True"
            kv_state_data["rook-ceph-mon"] = self._get_readable_json_dump(secret)

        return kv_state_data

    @staticmethod
    def register_execution_state(
        machine: Machine, state_name: str, handler: ModuleHandler, **kwargs: Any
    ) -> None:
        ModuleHandler.register_execution_state(
            machine, state_name, handler, tags=["configmap", "secret"]
        )

    @staticmethod
    def register_preflight_state(
        machine: Machine, state_name: str, handler: ModuleHandler, **kwargs: Any
    ) -> None:
        ModuleHandler.register_preflight_state(
            machine, state_name, handler, tags=["configmap"]
        )
