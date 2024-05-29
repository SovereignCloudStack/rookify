# -*- coding: utf-8 -*-

from dill import Pickler, Unpickler
from transitions import MachineError
from transitions import Machine as _Machine
from transitions.extensions.states import add_state_features, Tags, Timeout
from typing import Any, Dict, IO, Optional, List
from ..logger import get_logger


@add_state_features(Tags, Timeout)
class Machine(_Machine):  # type: ignore
    STATE_NAME_EXECUTION_PREFIX = "Execution"
    STATE_NAME_PREFLIGHT_PREFIX = "Preflight"

    def __init__(self, machine_pickle_file: Optional[str] = None) -> None:
        self._machine_pickle_file = machine_pickle_file
        self._execution_states: List[str] = []
        self._preflight_states: List[str] = []

        _Machine.__init__(self, states=["uninitialized"], initial="uninitialized")

    def add_execution_state(self, name: str, **kwargs: Dict[str, Any]) -> None:
        self._execution_states.append(self.__class__.state_cls(name, **kwargs))

    def add_preflight_state(self, name: str, **kwargs: Dict[str, Any]) -> None:
        self._preflight_states.append(self.__class__.state_cls(name, **kwargs))

    def execute(self) -> None:
        for state in self._preflight_states + self._execution_states:
            self.add_state(state)

        self.add_state("migrated")
        self.add_ordered_transitions(loop=False)

        if self._machine_pickle_file is None:
            self._execute()
        else:
            with open(self._machine_pickle_file, "ab+") as file:
                self._execute(file)

    def _execute(self, pickle_file: Optional[IO[Any]] = None) -> None:
        states_data = {}

        if pickle_file is not None and pickle_file.tell() > 0:
            pickle_file.seek(0)

            states_data = Unpickler(pickle_file).load()
            self._restore_state_data(states_data)

        try:
            while True:
                self.next_state()

                if pickle_file is not None:
                    state_data = self._get_state_tags_data(self.state)

                    if len(state_data) > 0:
                        states_data[self.state] = state_data
        except MachineError:
            if self.state != "migrated":
                raise
        finally:
            if pickle_file is not None:
                get_logger().debug("Storing state data: {0}".format(states_data))
                pickle_file.truncate(0)

                Pickler(pickle_file).dump(states_data)

    def _get_state_tags_data(self, name: str) -> Dict[str, Any]:
        data = {}
        state = self.get_state(name)

        if len(state.tags) > 0:
            for tag in state.tags:
                data[tag] = getattr(state, tag)

        return data

    def get_execution_state(self, name: Optional[str] = None) -> Any:
        if name is None:
            name = self.state
        else:
            name = self.__class__.STATE_NAME_EXECUTION_PREFIX + name

        return self.get_state(name)

    def get_preflight_state(self, name: Optional[str] = None) -> Any:
        if name is None:
            name = self.state
        else:
            name = self.__class__.STATE_NAME_PREFLIGHT_PREFIX + name

        return self.get_state(name)

    def _restore_state_data(self, data: Dict[str, Any]) -> None:
        for state_name in data:
            try:
                state = self.get_state(state_name)

                for tag in data[state_name]:
                    setattr(state, tag, data[state_name][tag])
            except Exception as exc:
                get_logger().debug(
                    "Restoring state data failed for '{0}': {1!r}".format(
                        state_name, exc
                    )
                )
