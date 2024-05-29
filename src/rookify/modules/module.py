# -*- coding: utf-8 -*-

import os
import yaml
import json
import abc
import rados
import kubernetes
import fabric
import jinja2
import structlog
from typing import Any, Dict, List, Optional

from ..logger import get_logger
from .machine import Machine


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

        def __getattr__(self, name: str) -> Any:
            return getattr(self.__ceph, name)

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

    def __init__(self, machine: Machine, config: Dict[str, Any]):
        """
        Construct a new 'ModuleHandler' object.

        :param machine: Machine object
        :param config: The global config file
        :return: returns nothing
        """
        self._config = config
        self._machine = machine

        self.__ceph: Optional[ModuleHandler.__Ceph] = None
        self.__k8s: Optional[ModuleHandler.__K8s] = None
        self.__ssh: Optional[ModuleHandler.__SSH] = None
        self.__logger = get_logger()

    @property
    def ceph(self) -> __Ceph:
        if self.__ceph is None:
            self.__ceph = ModuleHandler.__Ceph(self._config["ceph"])
        return self.__ceph

    @property
    def machine(self) -> Machine:
        return self._machine

    @property
    def k8s(self) -> __K8s:
        if self.__k8s is None:
            self.__k8s = ModuleHandler.__K8s(self._config["kubernetes"])
        return self.__k8s

    @property
    def logger(self) -> structlog.getLogger:
        return self.__logger

    @property
    def ssh(self) -> __SSH:
        if self.__ssh is None:
            self.__ssh = ModuleHandler.__SSH(self._config["ssh"])
        return self.__ssh

    @abc.abstractmethod
    def preflight(self) -> None:
        """
        Run the modules preflight check
        """
        pass

    @abc.abstractmethod
    def execute(self) -> None:
        """
        Executes the modules tasks

        :return: returns result
        """
        pass

    def load_template(self, filename: str, **variables: Any) -> __Template:
        template_path = os.path.join(os.path.dirname(__file__), "templates", filename)
        template = ModuleHandler.__Template(template_path)
        template.render(**variables)
        return template

    @classmethod
    def register_states(cls, machine: Machine, config: Dict[str, Any]) -> None:
        """
        Register states for transitions
        """

        state_name = cls.STATE_NAME if hasattr(cls, "STATE_NAME") else cls.__name__

        handler = cls(machine, config)
        preflight_state_name = None
        execution_state_name = None

        if hasattr(cls, "preflight") and not getattr(
            cls.preflight, "__isabstractmethod__", False
        ):
            preflight_state_name = Machine.STATE_NAME_PREFLIGHT_PREFIX + state_name

        if hasattr(cls, "execute") and not getattr(
            cls.execute, "__isabstractmethod__", False
        ):
            execution_state_name = Machine.STATE_NAME_EXECUTION_PREFIX + state_name

        if preflight_state_name is None and execution_state_name is None:
            get_logger().warn(
                "Not registering state {0} because ModuleHandler has no expected callables".format(
                    state_name
                )
            )
        else:
            get_logger().debug("Registering states for {0}".format(state_name))

            if preflight_state_name is not None:
                cls.register_preflight_state(machine, preflight_state_name, handler)

            if execution_state_name is not None:
                cls.register_execution_state(machine, execution_state_name, handler)

    @staticmethod
    def register_preflight_state(
        machine: Machine, state_name: str, handler: Any, **kwargs: Any
    ) -> None:
        """
        Register state for transitions
        """

        machine.add_preflight_state(state_name, on_enter=handler.preflight, **kwargs)

    @staticmethod
    def register_execution_state(
        machine: Machine, state_name: str, handler: Any, **kwargs: Any
    ) -> None:
        """
        Register state for transitions
        """

        machine.add_execution_state(state_name, on_enter=handler.execute, **kwargs)
