# -*- coding: utf-8 -*-

import json
from collections.abc import Callable
from rookify.modules.exception import ModuleException
from typing import Any, Dict, Tuple


class MockCeph(object):
    def __init__(
        self,
        config: Dict[str, Any],
        _callable: Callable[[str, bytes], Tuple[int, bytes, str]],
    ):
        if not callable(_callable):
            raise RuntimeError("Handler function given is invalid")

        self._callback_handler = _callable

    def mon_command(self, command: str, inbuf: bytes, **kwargs: Any) -> Any:
        ret, outbuf, outstr = self._callback_handler(command, inbuf, **kwargs)
        if ret != 0:
            raise ModuleException("Ceph did return an error: {0!r}".format(outbuf))

        data = json.loads(outbuf)
        assert isinstance(data, dict) or isinstance(data, list)
        return data
