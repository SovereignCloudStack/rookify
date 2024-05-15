# -*- coding: utf-8 -*-

from typing import Any, Dict
from ..module import ModuleHandler


class MigrateOSDsHandler(ModuleHandler):
    REQUIRES = ["analyze_ceph"]

    def execute(self) -> Any:
        osd_config: Dict[str, Any] = {}
        state_data = self.machine.get_state("AnalyzeCephHandler").data

        for node, osds in state_data["node"]["ls"]["osd"].items():
            osd_config[node] = {"osds": {}}
            for osd in osds:
                osd_config[node]["osds"][osd] = dict()

        for osd in state_data["osd"]["dump"]["osds"]:
            number = osd["osd"]
            uuid = osd["uuid"]
            for host in osd_config.values():
                if number in host["osds"]:
                    host["osds"][number]["uuid"] = uuid
                    break

        for node, values in osd_config.items():
            devices = state_data["ssh"]["osd"][node]["devices"]
            for osd in values["osds"].values():
                for device in devices:
                    if osd["uuid"] in device:
                        osd["device"] = device
                        break

        self.logger.info(osd_config)
