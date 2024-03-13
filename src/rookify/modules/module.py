# -*- coding: utf-8 -*-

import json
import abc
import rados
import kubernetes
import fabric
from typing import Any


class ModuleException(Exception):
    pass


class ModuleHandler:
    """
    ModuleHandler is an abstract class that modules have to extend.
    """

    class __Ceph:
        def __init__(self, config: dict[str, Any]):
            try:
                self.__ceph = rados.Rados(
                    conffile=config["conf_file"], conf={"keyring": config["keyring"]}
                )
                self.__ceph.connect()
            except rados.ObjectNotFound as err:
                raise ModuleException(f"Could not connect to ceph: {err}")

        def mon_command(self, command: str, **kwargs: dict[str, str]) -> dict[str, Any]:
            cmd = {"prefix": command, "format": "json"}
            cmd.update(**kwargs)
            result = self.__ceph.mon_command(json.dumps(cmd), b"")
            if result[0] != 0:
                raise ModuleException(f"Ceph did return an error: {result}")
            return json.loads(result[1])

    class __K8s:
        def __init__(self, config: dict):
            k8s_config = kubernetes.client.Configuration()
            k8s_config.api_key = config["api_key"]
            k8s_config.host = config["host"]
            self.__client = kubernetes.client.ApiClient(k8s_config)

        @property
        def CoreV1Api(self) -> kubernetes.client.CoreV1Api:
            return kubernetes.client.CoreV1Api(self.__client)

        @property
        def AppsV1Api(self) -> kubernetes.client.AppsV1Api:
            return kubernetes.client.AppsV1Api(self.__client)

        @property
        def NodeV1Api(self) -> kubernetes.client.NodeV1Api:
            return kubernetes.client.NodeV1Api(self.__client)

    class __SSH:
        def __init__(self, config: dict):
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

    def __init__(self, config: dict, data: dict):
        """
        Construct a new 'ModuleHandler' object.

        :param module_data: The config and results from modules
        :return: returns nothing
        """
        self._config = config
        self._data = data
        self.__ceph: self.__Ceph = None  # type: ignore
        self.__k8s: self.__K8s = None  # type: ignore
        self.__ssh: self.__SSH = None  # type: ignore

    @abc.abstractmethod
    def preflight_check(self) -> None:
        """
        Run the modules preflight check
        """
        pass

    @abc.abstractmethod
    def run(self) -> dict:
        """
        Run the modules tasks

        :return: returns result
        """
        pass

    @property
    def ceph(self) -> __Ceph:
        if self.__ceph is None:
            self.__ceph = self.__Ceph(self._config["ceph"])
        return self.__ceph

    @property
    def k8s(self) -> __K8s:
        if self.__k8s is None:
            self.__k8s = self.__K8s(self._config["kubernetes"])
        return self.__k8s

    @property
    def ssh(self) -> __SSH:
        if self.__ssh is None:
            self.__ssh = self.__SSH(self._config["ssh"])
        return self.__ssh
