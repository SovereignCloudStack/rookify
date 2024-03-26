# -*- coding: utf-8 -*-

from paramiko import Channel
from typing import Any
from unittest import TestCase

from .mock_ssh_server import MockSSHServer


class TestMockSSHServer(TestCase):
    ssh_client: Any = None
    ssh_server: Any = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.ssh_server = MockSSHServer()
        cls.ssh_client = cls.ssh_server.client

    @classmethod
    def tearDownClass(cls) -> None:
        cls.ssh_server.close()

    def setUp(self) -> None:
        self.__class__.ssh_server.handle_exec_requests_with_callback(
            self._command_callback
        )

    def tearDown(self) -> None:
        self.__class__.ssh_server.stop_exec_requests_handler()

    def _command_callback(self, command: bytes, channel: Channel) -> None:
        if command == b"test":
            channel.send(b"ok\n")

    def test_self(self) -> None:
        _, stdout, _ = self.__class__.ssh_client.exec_command("test")
        self.assertEqual(stdout.readline(), "ok\n")
