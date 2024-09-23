# -*- coding: utf-8 -*-

from collections import OrderedDict
from typing import Any, Dict, Optional
from ..machine import Machine
from ..module import ModuleHandler


class AnalyzeCephHandler(ModuleHandler):
    def _process_command_result(
        self, state_data: Any, command: str, value: Optional[Any] = None
    ) -> bool:
        """
        Helper method to process commands by either setting or checking state data.
        """

        command_parts = command.split(" ")
        state_structure_data = state_data  # the root of the data structure

        # Traverse the dictionary structure based on command parts
        for idx, key in enumerate(command_parts):
            # Last part of the command
            if len(command_parts) == idx + 1:
                if value is None:
                    return key in state_structure_data

                state_structure_data[key] = value
            else:
                if key not in state_structure_data:
                    state_structure_data[key] = {}

                state_structure_data = state_structure_data[key]

        return True

    def preflight(self) -> Any:
        state = self.machine.get_preflight_state("AnalyzeCephHandler")

        if getattr(state, "data", None) is not None:
            return

        commands = ["fs ls", "node ls", "report"]
        state.data = {}

        # Execute each command and store the result
        for command in commands:
            result = self.ceph.mon_command(command)
            self._process_command_result(state.data, command, result)

        self.logger.info("AnalyzeCephHandler ran successfully.")

    def get_readable_key_value_state(self) -> Dict[str, str]:
        state = self.machine.get_preflight_state("AnalyzeCephHandler")

        kv_state_data = OrderedDict()

        if "report" not in state.data:
            kv_state_data["Ceph report"] = "Not analyzed yet"
        else:
            kv_state_data["Ceph report"] = self._get_readable_json_dump(
                state.data["report"]
            )

        if "node" not in state.data or "ls" not in state.data["node"]:
            kv_state_data["Ceph node ls"] = "Not analyzed yet"
        else:
            kv_state_data["Ceph node ls"] = self._get_readable_json_dump(
                state.data["node"]["ls"]
            )

        if "fs" not in state.data or "ls" not in state.data["fs"]:
            kv_state_data["Ceph fs ls"] = "Not analyzed yet"
        else:
            kv_state_data["Ceph fs ls"] = self._get_readable_json_dump(
                state.data["fs"]["ls"]
            )

        return kv_state_data

    @staticmethod
    def register_preflight_state(
        machine: Machine, state_name: str, handler: ModuleHandler, **kwargs: Any
    ) -> None:
        ModuleHandler.register_preflight_state(
            machine, state_name, handler, tags=["data"]
        )
