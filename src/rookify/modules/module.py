# -*- coding: utf-8 -*-

import abc
import json
import os
import structlog
from typing import Any, Dict, Optional
from ..logger import get_logger
from . import get_modules
from .ceph import Ceph
from .k8s import K8s
from .machine import Machine
from .ssh import SSH
from .template import Template


class ModuleHandler(object):
    """
    ModuleHandler is an abstract class that modules have to extend.
    """

    def __init__(self, machine: Machine, config: Dict[str, Any]):
        """
        Construct a new 'ModuleHandler' object.

        :param machine: Machine object
        :param config: The global config file
        :return: returns nothing
        """
        self._config = config
        self._machine = machine

        self._ceph: Optional[Ceph] = None
        self._k8s: Optional[K8s] = None
        self._ssh: Optional[SSH] = None
        self._logger = get_logger()

    @property
    def ceph(self) -> Ceph:
        if self._ceph is None:
            self._ceph = Ceph(self._config["ceph"])
        return self._ceph

    @property
    def machine(self) -> Machine:
        return self._machine

    @property
    def k8s(self) -> K8s:
        if self._k8s is None:
            self._k8s = K8s(self._config)
        return self._k8s

    @property
    def logger(self) -> structlog.getLogger:
        return self._logger

    @property
    def ssh(self) -> SSH:
        if self._ssh is None:
            self._ssh = SSH(self._config["ssh"])
        return self._ssh

    def _get_readable_json_dump(self, data: Any) -> Any:
        return json.dumps(data, default=repr, sort_keys=True, indent="\t")

    def get_readable_key_value_state(self) -> Optional[Dict[str, str]]:
        """
        Run the modules status check
        """

        return None

    @abc.abstractmethod
    def preflight(self) -> None:
        """
        Run the modules preflight check
        """
        pass

    def execute(self) -> None:
        """
        Executes the modules tasks

        :return: returns result
        """
        pass

    def load_template(self, filename: str, **variables: Any) -> Template:
        template_path = os.path.join(
            os.path.dirname(__file__),
            self.__class__.__module__.rsplit(".", 2)[1],
            "templates",
            filename,
        )
        template = Template(template_path)
        template.render(**variables)
        return template

    @classmethod
    def register_states(
        cls,
        machine: Machine,
        config: Dict[str, Any],
        show_progress: Optional[bool] = False,
    ) -> None:
        """
        Register states for transitions
        """

        state_name = cls.STATE_NAME if hasattr(cls, "STATE_NAME") else cls.__name__

        handler = cls(machine, config)
        preflight_state_name = None
        execution_state_name = None

        if hasattr(cls, "preflight") and not getattr(
            cls.preflight, "__isabstractmethod__", False
        ):
            preflight_state_name = Machine.STATE_NAME_PREFLIGHT_PREFIX + state_name

        if hasattr(cls, "execute") and not getattr(
            cls.execute, "__isabstractmethod__", False
        ):
            execution_state_name = Machine.STATE_NAME_EXECUTION_PREFIX + state_name

        if preflight_state_name is None and execution_state_name is None:
            get_logger().warn(
                "Not registering state {0} because ModuleHandler has no expected callables".format(
                    state_name
                )
            )
        else:
            if preflight_state_name is not None:
                cls.register_preflight_state(machine, preflight_state_name, handler)

            if execution_state_name is not None:
                cls.register_execution_state(machine, execution_state_name, handler)

    @staticmethod
    def register_preflight_state(
        machine: Machine, state_name: str, handler: Any, **kwargs: Any
    ) -> None:
        """
        Register state for transitions
        """

        machine.add_preflight_state(state_name, on_enter=handler.preflight, **kwargs)

    @staticmethod
    def register_execution_state(
        machine: Machine, state_name: str, handler: Any, **kwargs: Any
    ) -> None:
        """
        Register state for transitions
        """

        machine.add_execution_state(state_name, on_enter=handler.execute, **kwargs)

    @staticmethod
    def show_states(machine: Machine, config: Dict[str, Any]) -> None:
        machine.register_states()
        modules = get_modules()

        for module in modules:
            module_handler = module.ModuleHandler(machine, config)

            if hasattr(module_handler, "get_readable_key_value_state"):
                state_data = module_handler.get_readable_key_value_state()

                if state_data is None:
                    continue

                for state_key, state_value in state_data.items():
                    print("{0}: {1}".format(state_key, state_value))
