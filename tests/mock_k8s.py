# -*- coding: utf-8 -*-

from collections.abc import Callable
from typing import Any


class MockK8s(object):
    def __init__(self, _callable: Callable[[str], Any], name: str = "") -> None:
        if not callable(_callable):
            raise RuntimeError("Handler function given is invalid")

        self._callback_handler = _callable
        self._attr_name = name

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self._callback_handler(self._attr_name, *args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        attr_name = (
            name if self._attr_name == "" else "{0}.{1}".format(self._attr_name, name)
        )

        return MockK8s(self._callback_handler, attr_name)
