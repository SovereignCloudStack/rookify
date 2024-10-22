# -*- coding: utf-8 -*-

from dill import Pickler, Unpickler
from transitions import MachineError, State
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
        self._execution_states: List[State] = []
        self._preflight_states: List[State] = []

        _Machine.__init__(self, states=["uninitialized"], initial="uninitialized")

    def add_execution_state(self, name: str, **kwargs: Any) -> None:
        self._execution_states.append(self.__class__.state_cls(name, **kwargs))

    def add_preflight_state(self, name: str, **kwargs: Any) -> None:
        self._preflight_states.append(self.__class__.state_cls(name, **kwargs))

    def execute(self, dry_run_mode: bool = False) -> None:
        states = self._preflight_states
        if not dry_run_mode:
            states = states + self._execution_states

        self._register_states(states)

        logger = get_logger()

        if self._machine_pickle_file is None:
            logger.info("Execution started without machine pickle file")
            self._execute()
        else:
            with open(self._machine_pickle_file, "ab+") as file:
                logger.info("Execution started with machine pickle file")
                self._execute(file)

    def _execute(self, pickle_file: Optional[IO[Any]] = None) -> None:
        states_data = {}

        if pickle_file is not None:
            self._restore_state_data(pickle_file)

        try:
            while True:
                try:
                    self.next_state()
                except:
                    raise
                finally:
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
                if hasattr(state, tag):
                    data[tag] = getattr(state, tag)

        return data

    def get_execution_state(self, name: str) -> Any:
        state_name = self.__class__.STATE_NAME_EXECUTION_PREFIX + name

        if state_name not in self.states:
            return None

        return self.get_state(state_name)

    def get_execution_state_data(
        self, name: str, tag: str, default_value: Any = None
    ) -> Any:
        return getattr(self.get_execution_state(name), tag, default_value)

    def get_preflight_state(self, name: str) -> Any:
        state_name = self.__class__.STATE_NAME_PREFLIGHT_PREFIX + name

        if state_name not in self.states:
            return None

        return self.get_state(state_name)

    def get_preflight_state_data(
        self, name: str, tag: str, default_value: Any = None
    ) -> Any:
        return getattr(self.get_preflight_state(name), tag, default_value)

    def register_states(self) -> None:
        self._register_states(self._preflight_states + self._execution_states)

        if self._machine_pickle_file is not None:
            with open(self._machine_pickle_file, "rb") as file:
                file.seek(1)
                self._restore_state_data(file)

    def _register_states(self, states: List[State]) -> None:
        logger = get_logger()

        for state in states:
            if state.name not in self.states:
                logger.debug("Registering state '{0}'".format(state.name))
                self.add_state(state)

        self.add_state("migrated")
        self.add_ordered_transitions(loop=False)

    """
Read pickle file if it exists, to continue from the stored state. It is
required that the position of the pointer of the pickle file given is not
at the start.
    """

    def _restore_state_data(self, pickle_file: IO[Any]) -> None:
        if pickle_file.tell() == 0:
            return None

        pickle_file.seek(0)

        data = Unpickler(pickle_file).load()

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
