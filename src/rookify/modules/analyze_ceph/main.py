# -*- coding: utf-8 -*-

import pickle
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

        self.logger.info("AnalyzeCephHandler ran successfully.")

    def show_progress(self) -> Any:
        try:
            # Retrieve the pickled state
            state = self.machine.get_preflight_state("AnalyzeCephHandler")
            # Unpickle the state
            state = pickle.loads(state)
        except Exception as e:
            self.logger.info("AnalyzeCephHandler has not run yet.")
            self.logger.debug(e)

        # Show the state
        self.logger.info("AnalyzeCephHandler ran successfully.")

    @staticmethod
    def register_preflight_state(
        machine: Machine, state_name: str, handler: ModuleHandler, **kwargs: Any
    ) -> None:
        ModuleHandler.register_preflight_state(
            machine, state_name, handler, tags=["data"]
        )

    @staticmethod
    def register_show_progress_state(
        machine: Machine, state_name: str, handler: ModuleHandler, **kwargs: Any
    ) -> None:
        ModuleHandler.register_show_progress_state(
            machine, state_name, handler, tags=["data"]
        )
