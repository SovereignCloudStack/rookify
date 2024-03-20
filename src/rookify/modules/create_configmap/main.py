# -*- coding: utf-8 -*-

from ..module import ModuleHandler, ModuleException
import kubernetes

from typing import Any


class CreateConfigMapHandler(ModuleHandler):
    def __create_configmap_definition(self) -> Any:
        pass

    def preflight(self) -> None:
        self.__cluster_name = self._config["rook"]["cluster"]["name"]
        self.__fsid = self._data["analyze_ceph"]["mon"]["dump"]["fsid"]

        # If the secret already exists, we have to abort to not override it
        try:
            self.k8s.core_v1_api.read_namespaced_secret(
                "rook-ceph-mon", self._config["rook"]["cluster"]["namespace"]
            )
        except kubernetes.client.exceptions.ApiException:
            pass
        else:
            raise ModuleException("Secret rook-ceph-mon already exists")

    def run(self) -> Any:
        # Get or create needed auth keys
        admin_auth = self.ceph.mon_command(
            "auth get-or-create-key",
            entity="client.admin",
            mon="allow *",
            mgr="allow *",
            mds="allow *",
        )

        mon_auth = self.ceph.mon_command(
            "auth get-or-create-key", entity="mon.", mon="allow *"
        )

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

        return secret.to_dict()
