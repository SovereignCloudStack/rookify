# -*- coding: utf-8 -*-

from typing import Any, Dict
from ..machine import Machine
from ..module import ModuleHandler


class AnalyzeCephHandler(ModuleHandler):
    def preflight(self) -> Any:
        commands = ["mon dump", "osd dump", "device ls", "fs dump", "node ls"]

        state = self.machine.get_preflight_state("AnalyzeCephHandler")
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

        self.logger.info("AnalyzeCephHandler ran successfully.")

    @staticmethod
    def register_preflight_state(
        machine: Machine, state_name: str, handler: ModuleHandler, **kwargs: Any
    ) -> None:
        ModuleHandler.register_preflight_state(
            machine, state_name, handler, tags=["data"]
        )
