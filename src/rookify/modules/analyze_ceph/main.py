# -*- coding: utf-8 -*-

from typing import Any, Optional
from ..machine import Machine
from ..module import ModuleHandler


class AnalyzeCephHandler(ModuleHandler):
    def _process_command(
        self, state_data: Any, command: str, value: Optional[Any] = None
    ) -> bool:
        """Helper method to process commands by either setting or checking state data."""
        parts = command.split(" ")
        current_level = state_data  # the root of the data structure

        # Traverse the dictionary structure based on command parts
        for idx, part in enumerate(parts):
            if len(parts) == idx + 1:  # Last part of the command
                if value is not None:
                    current_level[part] = value
                else:
                    return part in current_level
            else:
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]

        return True

    def preflight(self) -> Any:
        commands = ["mon dump", "osd dump", "device ls", "fs ls", "node ls"]
        state = self.machine.get_preflight_state("AnalyzeCephHandler")
        state.data = {}

        # Execute each command and store the result
        for command in commands:
            result = self.ceph.mon_command(command)
            self._process_command(state.data, command, result)

        self.logger.info("AnalyzeCephHandler ran successfully.")

    def status(self) -> Any:
        commands = ["mon dump", "osd dump", "device ls", "fs ls", "node ls"]
        state = self.machine.get_preflight_state("AnalyzeCephHandler")

        # Check if all expected commands have been run
        all_commands_found = True
        for command in commands:
            if not self._process_command(state.data, command):
                all_commands_found = False
                break

        # Log the status
        if all_commands_found:
            self.logger.info("AnalyzeCephHandler has already been run.")
            self.logger.info("Current state data: %s", state.data)
        else:
            self.logger.info("Progress: Not all commands have been run yet.")

    @staticmethod
    def register_preflight_state(
        machine: Machine, state_name: str, handler: ModuleHandler, **kwargs: Any
    ) -> None:
        ModuleHandler.register_preflight_state(
            machine, state_name, handler, tags=["data"]
        )
