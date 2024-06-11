# -*- coding: utf-8 -*-

import unittest

from rookify.modules.example.main import ExampleHandler
from rookify.modules.exception import ModuleException
from rookify.modules.machine import Machine


class TestExampleHandler(unittest.TestCase):
    def test_preflight(self) -> None:
        with self.assertRaises(ModuleException):
            ExampleHandler(Machine(), {}).preflight()
