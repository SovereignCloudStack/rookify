# -*- coding: utf-8 -*-

from typing import Any, Dict, Tuple
from unittest import TestCase

from .mock_ceph import MockCeph


class TestMockCeph(TestCase):
    ceph: Any = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.ceph = MockCeph({})

    def setUp(self) -> None:
        self.__class__.ceph.handle_with_callback(self._command_callback)

    def tearDown(self) -> None:
        self.__class__.ceph.stop_handler()

    def _command_callback(
        self, command: str, inbuf: bytes, **kwargs: Dict[Any, Any]
    ) -> Tuple[int, bytes, str]:
        if command == "test":
            return 0, b'["ok"]', ""
        return -1, b'["Command not found"]', ""

    def test_self(self) -> None:
        res = self.__class__.ceph.mon_command("test", b"")
        self.assertEqual(res, ["ok"])
