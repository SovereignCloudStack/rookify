# -*- coding: utf-8 -*-

from rookify.modules.k8s_prerequisites_check.main import K8sPrerequisitesCheckHandler
from typing import Any
from .mock_k8s import MockK8s


# Note: currently this test works with pytest but not with unittest, which is not able to import needed classes
class MockK8sPrerequisitesCheckHandler(K8sPrerequisitesCheckHandler):
    def __init__(self, request_callback: Any, *args: Any, **kwargs: Any) -> None:
        K8sPrerequisitesCheckHandler.__init__(self, *args, **kwargs)
        self._k8s = MockK8s(request_callback)  # type: ignore
