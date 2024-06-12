# -*- coding: utf-8 -*-

import pytest

from rookify.modules.example.main import ExampleHandler
from rookify.modules.exception import ModuleException
from rookify.modules.machine import Machine


def test_preflight() -> None:
    with pytest.raises(ModuleException):
        ExampleHandler(Machine(), {}).preflight()
