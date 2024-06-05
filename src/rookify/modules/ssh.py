# -*- coding: utf-8 -*-

import fabric
from typing import Any, Dict
from .exception import ModuleException


class SSH:
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
