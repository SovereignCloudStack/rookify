from rookify.modules.k8s_prerequisites_check.main import K8sPrerequisitesCheckHandler
from typing import Any


# Note: currently this test works with pytest but not with unittest, which is not able to import needed classes
class MockK8sPrerequisitesCheckHandler(K8sPrerequisitesCheckHandler):  # type: ignore
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Set a mock object as the value of the k8s attribute
        self._k8s = None

    @property
    def k8s(self) -> Any:
        return self._k8s

    @k8s.setter
    def k8s(self, value: Any) -> None:
        self._k8s = value

    def preflight(self) -> None:
        # Call original preflight method
        super().preflight()
        # Add additional mocking behavior here if needed
        pass
