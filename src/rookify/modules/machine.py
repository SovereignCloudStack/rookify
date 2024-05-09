# -*- coding: utf-8 -*-

from transitions import MachineError
from transitions import Machine as _Machine
from transitions.extensions.states import add_state_features, Tags, Timeout
from typing import Any, Dict


@add_state_features(Tags, Timeout)
class Machine(_Machine):  # type: ignore
    def __init__(self) -> None:
        _Machine.__init__(self, states=["uninitialized"], initial="uninitialized")

    def add_migrating_state(self, name: Any, **kwargs: Dict[str, Any]) -> None:
        if not isinstance(name, str):
            raise MachineError("Migration state name must be string")
        self.add_state(name, **kwargs)

    def execute(self) -> None:
        self.add_state("migrated")
        self.add_ordered_transitions(loop=False)

        try:
            while True:
                self.next_state()
        except MachineError:
            if self.state != "migrated":
                raise
