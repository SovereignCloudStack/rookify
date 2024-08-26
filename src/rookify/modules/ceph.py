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

    def _json_command(self, handler: Any, *args: Any) -> Dict[str, Any] | List[Any]:
        result = handler(*args)
        if result[0] != 0:
            raise ModuleException(f"Ceph did return an error: {result}")

        data = {}

        if len(result) > 0 and result[1] != b"":
            data = json.loads(result[1])
            assert isinstance(data, dict) or isinstance(data, list)

        return data

    def get_osd_pool_configurations_from_osd_dump(
        self, dump_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        osd_pools = {osd_pool["pool_name"]: osd_pool for osd_pool in dump_data["pools"]}

        erasure_code_profiles = dump_data["erasure_code_profiles"]

        for osd_pool_name in osd_pools:
            osd_pool = osd_pools[osd_pool_name]

            osd_pool["erasure_code_configuration"] = erasure_code_profiles.get(
                osd_pool["erasure_code_profile"], erasure_code_profiles["default"]
            )

            if osd_pool["erasure_code_configuration"].get("plugin") != "jerasure":
                raise ModuleException(
                    "Unsupported Ceph erasure code profile plugin in use"
                )

        return osd_pools

    def mon_command(self, command: str, **kwargs: Any) -> Dict[str, Any] | List[Any]:
        cmd = {"prefix": command, "format": "json"}
        cmd.update(**kwargs)
        return self._json_command(self.__ceph.mon_command, json.dumps(cmd), b"")

    def mgr_command(self, command: str, **kwargs: Any) -> Dict[str, Any] | List[Any]:
        cmd = {"prefix": command, "format": "json"}
        cmd.update(**kwargs)
        return self._json_command(self.__ceph.mgr_command, json.dumps(cmd), b"")

    def osd_command(
        self, osd_id: int, command: str, **kwargs: Any
    ) -> Dict[str, Any] | List[Any]:
        cmd = {"prefix": command, "format": "json"}
        cmd.update(**kwargs)
        return self._json_command(self.__ceph.osd_command, osd_id, json.dumps(cmd), b"")
