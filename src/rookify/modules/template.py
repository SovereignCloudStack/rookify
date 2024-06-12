# -*- coding: utf-8 -*-

import yaml
import jinja2
from typing import Any, Optional
from .exception import ModuleException


class Template:
    def __init__(self, template_path: str):
        self.__result_raw: Optional[str] = None
        self.__result_yaml: Optional[Any] = None
        self.__template_path: str = template_path
        with open(template_path) as file:
            self.__template = jinja2.Template(file.read())

    def render(self, **variables: Any) -> None:
        self.__result_raw = self.__template.render(**variables)
        self.__result_yaml = None

    @property
    def raw(self) -> str:
        if not self.__result_raw:
            raise ModuleException("Template was not rendered")
        return self.__result_raw

    @property
    def yaml(self) -> Any:
        if not self.__result_yaml:
            self.__result_yaml = yaml.safe_load(self.raw)
        return self.__result_yaml
