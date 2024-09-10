# -*- coding: utf-8 -*-

from typing import Any
from unittest import TestCase

from .mock_k8s import MockK8s


class TestMockK8s(TestCase):
    def setUp(self) -> None:
        self.k8s = MockK8s(self._request_callback)

    def _request_callback(self, method: str, *args: Any, **kwargs: Any) -> Any:
        if method == "core_v1_api.test":
            return True
        return None

    def test_self(self) -> None:
        res = self.k8s.core_v1_api.test()
        self.assertEqual(res, True)
