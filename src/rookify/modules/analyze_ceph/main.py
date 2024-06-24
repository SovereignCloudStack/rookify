# -*- coding: utf-8 -*-

from typing import Any
from ..machine import Machine
from ..module import ModuleHandler


class AnalyzeCephHandler(ModuleHandler):
    def preflight(self) -> Any:
        commands = ["mon dump", "osd dump", "device ls", "fs ls", "node ls"]

        state = self.machine.get_preflight_state("AnalyzeCephHandler")
        state.data = {}

        for command in commands:
            parts = command.split(" ")
            leaf = state.data

            for idx, part in enumerate(parts):
                if len(parts) == idx + 1:
                    leaf[part] = self.ceph.mon_command(command)
                else:
                    if part not in leaf:
                        leaf[part] = {}
                    leaf = leaf[part]

        self.logger.debug("AnalyzeCephHandler commands executed")

        state.data["ssh"] = {}
        state.data["ssh"]["osd"] = {}

        for node, values in state.data["node"]["ls"]["osd"].items():
            devices = self.ssh.command(node, "find /dev/ceph-*/*").stdout.splitlines()
            state.data["ssh"]["osd"][node] = {"devices": devices}

        self.logger.info("AnalyzeCephHandler ran successfully.")

    @staticmethod
    def register_preflight_state(
        machine: Machine, state_name: str, handler: ModuleHandler, **kwargs: Any
    ) -> None:
        ModuleHandler.register_preflight_state(
            machine, state_name, handler, tags=["data"]
        )
