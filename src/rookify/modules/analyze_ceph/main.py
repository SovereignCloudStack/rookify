# -*- coding: utf-8 -*-

from collections import OrderedDict
from typing import Any, Dict, Optional
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

    def get_readable_key_value_state(self) -> Dict[str, str]:
        state = self.machine.get_preflight_state("AnalyzeCephHandler")

        kv_state_data = OrderedDict()

        if "mon" not in state.data or "dump" not in state.data["mon"]:
            kv_state_data["ceph mon dump"] = "Not analyzed yet"
        else:
            kv_state_data["ceph mon dump"] = self._get_readable_json_dump(
                state.data["mon"]["dump"]
            )

        if "osd" not in state.data or "dump" not in state.data["osd"]:
            kv_state_data["ceph osd dump"] = "Not analyzed yet"
        else:
            kv_state_data["ceph osd dump"] = self._get_readable_json_dump(
                state.data["osd"]["dump"]
            )

        if "device" not in state.data or "ls" not in state.data["device"]:
            kv_state_data["OSD devices"] = "Not analyzed yet"
        else:
            kv_state_data["OSD devices"] = self._get_readable_json_dump(
                state.data["device"]["ls"]
            )

        return kv_state_data

    @staticmethod
    def register_preflight_state(
        machine: Machine, state_name: str, handler: ModuleHandler, **kwargs: Any
    ) -> None:
        ModuleHandler.register_preflight_state(
            machine, state_name, handler, tags=["data"]
        )
