# -*- coding: utf-8 -*-

import os
import yaml
import json
import abc
import rados
import kubernetes
import fabric
import jinja2
from typing import Any, Dict, List, Optional


class ModuleException(Exception):
    pass


class ModuleHandler:
    """
    ModuleHandler is an abstract class that modules have to extend.
    """

    class __Ceph:
        def __init__(self, config: Dict[str, Any]):
            try:
                self.__ceph = rados.Rados(
                    conffile=config["config"], conf={"keyring": config["keyring"]}
                )
                self.__ceph.connect()
            except rados.ObjectNotFound as err:
                raise ModuleException(f"Could not connect to ceph: {err}")

        def mon_command(
            self, command: str, **kwargs: str
        ) -> Dict[str, Any] | List[Any]:
            cmd = {"prefix": command, "format": "json"}
            cmd.update(**kwargs)
            result = self.__ceph.mon_command(json.dumps(cmd), b"")
            if result[0] != 0:
                raise ModuleException(f"Ceph did return an error: {result}")
            data = json.loads(result[1])
            assert isinstance(data, dict) or isinstance(data, list)
            return data

    class __K8s:
        def __init__(self, config: Dict[str, Any]):
            k8s_config = kubernetes.config.load_kube_config(
                config_file=config["config"]
            )
            self.__client = kubernetes.client.ApiClient(k8s_config)
            self.__dynamic_client: Optional[kubernetes.dynamic.DynamicClient] = None

        @property
        def core_v1_api(self) -> kubernetes.client.CoreV1Api:
            return kubernetes.client.CoreV1Api(self.__client)

        @property
        def apps_v1_api(self) -> kubernetes.client.AppsV1Api:
            return kubernetes.client.AppsV1Api(self.__client)

        @property
        def node_v1_api(self) -> kubernetes.client.NodeV1Api:
            return kubernetes.client.NodeV1Api(self.__client)

        @property
        def custom_objects_api(self) -> kubernetes.client.CustomObjectsApi:
            return kubernetes.client.CustomObjectsApi(self.__client)

        @property
        def dynamic_client(self) -> kubernetes.dynamic.DynamicClient:
            if not self.__dynamic_client:
                self.__dynamic_client = kubernetes.dynamic.DynamicClient(self.__client)
            return self.__dynamic_client

        def crd_api(
            self, api_version: str, kind: str
        ) -> kubernetes.dynamic.resource.Resource:
            return self.dynamic_client.resources.get(api_version=api_version, kind=kind)

        def crd_api_apply(
            self, manifest: Dict[Any, Any]
        ) -> kubernetes.dynamic.resource.ResourceInstance:
            """
            This applies a manifest for custom CRDs
            See https://github.com/kubernetes-client/python/issues/1792 for more information
            :param manifest: Dict of the kubernetes manifest
            """
            api_version = manifest["apiVersion"]
            kind = manifest["kind"]
            resource_name = manifest["metadata"]["name"]
            namespace = manifest["metadata"]["namespace"]
            crd_api = self.crd_api(api_version=api_version, kind=kind)

            try:
                crd_api.get(namespace=namespace, name=resource_name)
                return crd_api.patch(
                    body=manifest, content_type="application/merge-patch+json"
                )
            except kubernetes.dynamic.exceptions.NotFoundError:
                return crd_api.create(body=manifest, namespace=namespace)

    class __SSH:
        def __init__(self, config: Dict[str, Any]):
            self.__config = config

        def command(self, host: str, command: str) -> fabric.runners.Result:
            try:
                address = self.__config["hosts"][host]["address"]
                user = self.__config["hosts"][host]["user"]
                port = (
                    self.__config["hosts"][host]["port"]
                    if "port" in self.__config["hosts"][host]
                    else 22
                )
                private_key = self.__config["private_key"]
            except KeyError as err:
                raise ModuleException(
                    f"Could not find settings for {host} in config: {err}"
                )
            connect_kwargs = {"key_filename": private_key}
            result = fabric.Connection(
                address, user=user, port=port, connect_kwargs=connect_kwargs
            ).run(command, hide=True)
            return result

    class __Template:
        def __init__(self, template_path: str):
            self.__result_raw: Optional[str] = None
            self.__result_yaml: Optional[Any] = None
            self.__template_path: str = template_path
            with open(template_path) as file:
                self.__template = jinja2.Template(file.read())

        def render(self, **variables: Any) -> None:
            self.__result_raw = self.__template.render(**variables)
            self.__result_yaml = None

        @property
        def raw(self) -> str:
            if not self.__result_raw:
                raise ModuleException("Template was not rendered")
            return self.__result_raw

        @property
        def yaml(self) -> Any:
            if not self.__result_yaml:
                self.__result_yaml = yaml.safe_load(self.raw)
            return self.__result_yaml

    def __init__(self, config: Dict[str, Any], data: Dict[str, Any], module_path: str):
        """
        Construct a new 'ModuleHandler' object.

        :param config: The global config file
        :param data: The output of modules required by this module
        :param module_path: The filesystem path of this module
        :return: returns nothing
        """
        self._config = config
        self._data = data
        self.__module_path = module_path
        self.__ceph: Optional[ModuleHandler.__Ceph] = None
        self.__k8s: Optional[ModuleHandler.__K8s] = None
        self.__ssh: Optional[ModuleHandler.__SSH] = None

    @abc.abstractmethod
    def preflight(self) -> None:
        """
        Run the modules preflight check
        """
        pass

    @abc.abstractmethod
    def run(self) -> Dict[str, Any]:
        """
        Run the modules tasks

        :return: returns result
        """
        pass

    @property
    def ceph(self) -> __Ceph:
        if self.__ceph is None:
            self.__ceph = ModuleHandler.__Ceph(self._config["ceph"])
        return self.__ceph

    @property
    def k8s(self) -> __K8s:
        if self.__k8s is None:
            self.__k8s = ModuleHandler.__K8s(self._config["kubernetes"])
        return self.__k8s

    @property
    def ssh(self) -> __SSH:
        if self.__ssh is None:
            self.__ssh = ModuleHandler.__SSH(self._config["ssh"])
        return self.__ssh

    def load_template(self, filename: str, **variables: Any) -> __Template:
        template_path = os.path.join(self.__module_path, "templates", filename)
        template = ModuleHandler.__Template(template_path)
        template.render(**variables)
        return template
