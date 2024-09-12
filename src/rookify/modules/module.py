# -*- coding: utf-8 -*-

import os
import abc
import structlog
from typing import Any, Dict, Optional
from ..logger import get_logger
from .ceph import Ceph
from .k8s import K8s
from .machine import Machine
from .ssh import SSH
from .template import Template


class ModuleHandler:
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

        self.__ceph: Optional[Ceph] = None
        self.__k8s: Optional[K8s] = None
        self.__ssh: Optional[SSH] = None
        self.__logger = get_logger()

    @property
    def ceph(self) -> Ceph:
        if self.__ceph is None:
            self.__ceph = Ceph(self._config["ceph"])
        return self.__ceph

    @property
    def machine(self) -> Machine:
        return self._machine

    @property
    def k8s(self) -> K8s:
        if self.__k8s is None:
            self.__k8s = K8s(self._config)
        return self.__k8s

    @property
    def logger(self) -> structlog.getLogger:
        return self.__logger

    @property
    def ssh(self) -> SSH:
        if self.__ssh is None:
            self.__ssh = SSH(self._config["ssh"])
        return self.__ssh

    @abc.abstractmethod
    def status(self) -> None:
        """
        Run the modules status check
        """
        pass

    @abc.abstractmethod
    def preflight(self) -> None:
        """
        Run the modules preflight check
        """
        pass

    @abc.abstractmethod
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
                if show_progress is True:
                    cls.register_status_state(machine, preflight_state_name, handler)
                else:
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
    def register_status_state(
        machine: Machine, state_name: str, handler: Any, **kwargs: Any
    ) -> None:
        """
        Register state for transitions
        """

        machine.add_preflight_state(state_name, on_enter=handler.status, **kwargs)

    @staticmethod
    def register_execution_state(
        machine: Machine, state_name: str, handler: Any, **kwargs: Any
    ) -> None:
        """
        Register state for transitions
        """

        machine.add_execution_state(state_name, on_enter=handler.execute, **kwargs)
