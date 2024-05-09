# -*- coding: utf-8 -*-

from typing import Any, Dict
from ..machine import Machine
from ..module import ModuleHandler


class AnalyzeCephHandler(ModuleHandler):
    def run(self) -> Any:
        commands = ["mon dump", "osd dump", "device ls", "fs dump", "node ls"]

        state = self.machine.get_state("AnalyzeCephHandler")
        state.data: Dict[str, Any] = {}  # type: ignore

        for command in commands:
            parts = command.split(" ")
            leaf = state.data
            for idx, part in enumerate(parts):
                if idx < len(parts) - 1:
                    leaf[part] = {}
                else:
                    leaf[part] = self.ceph.mon_command(command)
                leaf = leaf[part]

        self.logger.debug("AnalyzeCephHandler commands executed")

        state.data["ssh"] = {}
        state.data["ssh"]["osd"] = {}

        for node, values in state.data["node"]["ls"]["osd"].items():
            devices = self.ssh.command(node, "find /dev/ceph-*/*").stdout.splitlines()
            state.data["ssh"]["osd"][node] = {"devices": devices}

        self.logger.info("AnalyzeCephHandler ran successfully.")

    @classmethod
    def register_state(
        _, machine: Machine, config: Dict[str, Any], **kwargs: Any
    ) -> None:
        """
        Register state for transitions
        """

        super().register_state(machine, config, tags=["data"])
