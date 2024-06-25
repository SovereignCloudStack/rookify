# -*- coding: utf-8 -*-

import json
import rados
from typing import Any, Dict, List
from .exception import ModuleException


class Ceph:
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

    def mon_command(self, command: str, **kwargs: str) -> Dict[str, Any] | List[Any]:
        cmd = {"prefix": command, "format": "json"}
        cmd.update(**kwargs)

        result = self.__ceph.mon_command(json.dumps(cmd), b"")

        if result[0] != 0:
            raise ModuleException(f"Ceph did return an error: {result}")

        data = {}

        if len(result) > 0 and result[1] != b"":
            data = json.loads(result[1])
            assert isinstance(data, dict) or isinstance(data, list)

        return data
