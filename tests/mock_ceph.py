# -*- coding: utf-8 -*-

import json
from collections.abc import Callable
from rookify.modules.module import ModuleException
from threading import RLock
from typing import Any, Dict, List, Optional, Tuple


class MockCeph(object):
    def __init__(self, config: Dict[str, Any]):
        self._callback_handler: Optional[
            Callable[[str, bytes], Tuple[int, bytes, str]]
        ] = None
        self._thread_lock = RLock()

    def handle_with_callback(
        self, _callable: Callable[[str, bytes], Tuple[int, bytes, str]]
    ) -> None:
        with self._thread_lock:
            if self._callback_handler is not None:
                raise RuntimeError("Callback handler already registered")

            self._callback_handler = _callable

    def mon_command(
        self, command: str, inbuf: bytes, **kwargs: Any
    ) -> Dict[str, Any] | List[Any]:
        if not callable(self._callback_handler):
            raise RuntimeError("Handler function given is invalid")

        ret, outbuf, outstr = self._callback_handler(command, inbuf, **kwargs)
        if ret != 0:
            raise ModuleException("Ceph did return an error: {0!r}".format(outbuf))

        data = json.loads(outbuf)
        assert isinstance(data, dict) or isinstance(data, list)
        return data

    def stop_handler(self) -> None:
        self._callback_handler = None
