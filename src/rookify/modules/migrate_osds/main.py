# -*- coding: utf-8 -*-

from ..module import ModuleHandler

from typing import Any, Dict


class MigrateOSDsHandler(ModuleHandler):
    def preflight_check(self) -> None:
        pass
        # result = self.ceph.mon_command("osd dump")
        # raise ModuleException('test error')

    def run(self) -> Dict[str, Any]:
        osd_config: Dict[str, Any] = dict()
        for node, osds in self._data["analyze_ceph"]["node"]["ls"]["osd"].items():
            osd_config[node] = {"osds": {}}
            for osd in osds:
                osd_config[node]["osds"][osd] = dict()

        for osd in self._data["analyze_ceph"]["osd"]["dump"]["osds"]:
            number = osd["osd"]
            uuid = osd["uuid"]
            for host in osd_config.values():
                if number in host["osds"]:
                    host["osds"][number]["uuid"] = uuid
                    break

        for node, values in osd_config.items():
            devices = self._data["analyze_ceph"]["ssh"]["osd"][node]["devices"]
            for osd in values["osds"].values():
                for device in devices:
                    if osd["uuid"] in device:
                        osd["device"] = device
                        break

        print(osd_config)
        return {}
