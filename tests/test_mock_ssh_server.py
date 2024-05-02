# -*- coding: utf-8 -*-

from paramiko import Channel
from unittest import TestCase

from .mock_ssh_server import MockSSHServer


class TestMockSSHServer(TestCase):
    def setUp(self) -> None:
        self.ssh_server = MockSSHServer(self._command_callback)
        self.ssh_client = self.ssh_server.client

    def tearDown(self) -> None:
        self.ssh_server.close()

    def _command_callback(self, command: bytes, channel: Channel) -> None:
        if command == b"test":
            channel.send(b"ok\n")

    def test_self(self) -> None:
        _, stdout, _ = self.ssh_client.exec_command("test")
        self.assertEqual(stdout.readline(), "ok\n")
