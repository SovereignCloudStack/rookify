# -*- coding: utf-8 -*-

from ..module import ModuleHandler

from typing import Any, Dict

from rookify.logger import getLogger


class AnalyzeCephHandler(ModuleHandler):
    def run(self) -> Any:
        commands = ["mon dump", "osd dump", "device ls", "fs dump", "node ls"]
        log = getLogger()

        results: Dict[str, Any] = dict()
        for command in commands:
            parts = command.split(" ")
            leaf = results
            for idx, part in enumerate(parts):
                if idx < len(parts) - 1:
                    leaf[part] = dict()
                else:
                    leaf[part] = self.ceph.mon_command(command)
                leaf = leaf[part]

        log.info("Dictionary created")
        results["ssh"] = dict()
        results["ssh"]["osd"] = dict()
        for node, values in results["node"]["ls"]["osd"].items():
            devices = self.ssh.command(node, "find /dev/ceph-*/*").stdout.splitlines()
            results["ssh"]["osd"][node] = {"devices": devices}
        log.info("AnalyzeCephHandler ran successfully.")
        return results
