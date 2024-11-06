# -*- coding: utf-8 -*-

import json
import rados
from typing import Any, Dict
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

        status_data = self.mon_command("status")

        self._fsid = status_data["fsid"]

        self._systemd_file_name_templates = config.get(
            "systemd_file_name_templates", {}
        )

    def __getattr__(self, name: str) -> Any:
        return getattr(self.__ceph, name)

    def _json_command(self, handler: Any, *args: Any) -> Any:
        result = handler(*args)
        if result[0] != 0:
            raise ModuleException(f"Ceph did return an error: {result}")

        data = {}

        if len(result) > 0 and result[1] != b"":
            data = json.loads(result[1])
            assert isinstance(data, dict) or isinstance(data, list)

        return data

    def get_systemd_mds_file_name(self, host: str) -> str:
        return self._get_systemd_template_file_name(
            self._systemd_file_name_templates.get("mds", "ceph-mds.target"),
            host,
        )

    def get_systemd_mgr_file_name(self, host: str) -> str:
        return self._get_systemd_template_file_name(
            self._systemd_file_name_templates.get("mgr", "ceph-mgr.target"),
            host,
        )

    def get_systemd_mon_file_name(self, host: str) -> str:
        return self._get_systemd_template_file_name(
            self._systemd_file_name_templates.get("mon", "ceph-mon.target"),
            host,
        )

    def get_systemd_osd_file_name(self, host: str, osd_id: int) -> str:
        file_name_template: str = self._systemd_file_name_templates.get(
            "osd", "ceph-osd@{0:d}.service".format(osd_id)
        )

        return file_name_template.format(fsid=self._fsid, host=host, osd_id=osd_id)

    def get_systemd_rgw_file_name(self, host: str) -> str:
        return self._get_systemd_template_file_name(
            self._systemd_file_name_templates.get("mon", "ceph-radosgw.target"),
            host,
        )

    def _get_systemd_template_file_name(
        self, file_name_template: str, host: str
    ) -> str:
        return file_name_template.format(fsid=self._fsid, host=host)

    def get_osd_pool_configurations_from_map(
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

    def mon_command(self, command: str, **kwargs: Any) -> Any:
        cmd = {"prefix": command, "format": "json"}
        cmd.update(**kwargs)
        return self._json_command(self.__ceph.mon_command, json.dumps(cmd), b"")

    def mgr_command(self, command: str, **kwargs: Any) -> Any:
        cmd = {"prefix": command, "format": "json"}
        cmd.update(**kwargs)
        return self._json_command(self.__ceph.mgr_command, json.dumps(cmd), b"")

    def osd_command(self, osd_id: int, command: str, **kwargs: Any) -> Any:
        cmd = {"prefix": command, "format": "json"}
        cmd.update(**kwargs)
        return self._json_command(self.__ceph.osd_command, osd_id, json.dumps(cmd), b"")
