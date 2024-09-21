# -*- coding: utf-8 -*-

from typing import Any
from ..machine import Machine
from ..module import ModuleHandler


class AnalyzeCephHandler(ModuleHandler):
    def preflight(self) -> None:
        state = self.machine.get_preflight_state("AnalyzeCephHandler")

        if getattr(state, "data", None) is not None:
            return

        commands = ["fs ls", "node ls", "report"]
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

        self.logger.info("AnalyzeCephHandler ran successfully.")

    @staticmethod
    def register_preflight_state(
        machine: Machine, state_name: str, handler: ModuleHandler, **kwargs: Any
    ) -> None:
        ModuleHandler.register_preflight_state(
            machine, state_name, handler, tags=["data"]
        )
