# -*- coding: utf-8 -*-


from collections.abc import Callable
from socket import AF_INET, IPPROTO_TCP, SO_REUSEADDR, SOCK_STREAM, SOL_SOCKET, socket
from threading import Event, RLock
from typing import Any, Optional

from paramiko import (  # type: ignore[attr-defined]
    AUTH_FAILED,
    AUTH_SUCCESSFUL,
    OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED,
    OPEN_SUCCEEDED,
    AutoAddPolicy,
    Channel,
    PKey,
    RSAKey,
    ServerInterface,
    SSHClient,
    Transport,
)


class MockSSHServer(ServerInterface):
    """An ssh server accepting the pre-generated key."""

    ssh_username = "pytest"
    ssh_key = RSAKey.generate(4096)

    def __init__(self, _callable: Callable[[bytes, Channel], None]) -> None:
        if not callable(_callable):
            raise RuntimeError("Handler function given is invalid")

        ServerInterface.__init__(self)

        self._callback_handler = _callable
        self._channel: Any = None
        self._client: Optional[SSHClient] = None
        self._command: Optional[bytes] = None
        self.event = Event()
        self._server_transport: Optional[Transport] = None
        self._thread_lock = RLock()

    def __del__(self) -> None:
        self.close()

    @property
    def client(self) -> SSHClient:
        with self._thread_lock:
            if self._client is None:
                connection_event = Event()

                server_socket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)
                server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
                server_socket.bind(("127.0.0.1", 0))
                server_socket.listen()

                server_address = server_socket.getsockname()

                client_socket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)
                client_socket.connect(server_address)

                (transport_socket, _) = server_socket.accept()

                self._server_transport = Transport(transport_socket)
                self._server_transport.add_server_key(self.__class__.ssh_key)
                self._server_transport.start_server(connection_event, self)

                self._client = SSHClient()
                self._client.set_missing_host_key_policy(AutoAddPolicy())

                self._client.connect(
                    server_address[0],
                    server_address[1],
                    username=self.__class__.ssh_username,
                    pkey=self.__class__.ssh_key,
                    sock=client_socket,
                )

                connection_event.wait()

        return self._client

    def check_channel_request(self, kind: str, chanid: int) -> int:
        if kind == "session":
            return OPEN_SUCCEEDED  # type: ignore[no-any-return]
        return OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED  # type: ignore[no-any-return]

    def check_auth_password(self, username: str, password: str) -> int:
        return AUTH_FAILED  # type: ignore[no-any-return]

    def check_auth_publickey(self, username: str, key: PKey) -> int:
        if username == self.__class__.ssh_username and key == self.__class__.ssh_key:
            return AUTH_SUCCESSFUL  # type: ignore[no-any-return]
        return AUTH_FAILED  # type: ignore[no-any-return]

    def check_channel_exec_request(self, channel: Channel, command: bytes) -> bool:
        if self.event.is_set():
            return False

        self.event.set()

        with self._thread_lock:
            self._channel = channel
            self._command = command

            if self._callback_handler is not None:
                self.handle_exec_request(self._callback_handler)

        return True

    def close(self) -> None:
        if self._server_transport is not None:
            self._server_transport.close()
            self._server_transport = None

    def get_allowed_auths(self, username: str) -> str:
        if username == self.__class__.ssh_username:
            return "publickey"
        return ""

    def handle_exec_request(self, _callable: Callable[[bytes, Channel], None]) -> None:
        if not callable(_callable):
            raise RuntimeError("Handler function given is invalid")

        _callable(self._command, self._channel)  # type: ignore[arg-type]

        if self._channel.recv_ready() is not True:
            self._channel.send(
                bytes("Command {0!r} invalid\n".format(self._command), "utf-8")
            )

        self._channel = None
        self._client = None

        self.event.clear()
