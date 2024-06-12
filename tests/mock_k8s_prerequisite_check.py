from rookify.modules.k8s_prerequisites_check.main import K8sPrerequisitesCheckHandler
from typing import Any


# Note: currently this test works with pytest but not with unittest, which is not able to import needed classes
class MockK8sPrerequisitesCheckHandler(K8sPrerequisitesCheckHandler):  # type: ignore[misc]
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._k8s = None

    @property
    def k8s(self) -> Any:
        return self._k8s

    @k8s.setter
    def k8s(self, value: Any) -> None:
        self._k8s = value

    def preflight(self) -> None:
        super().preflight()
        pass

    # Note: This solves the error 'cannot instantiate abstract class "MockK8sPrerequisitesCheckHandler" with abstract attribute "execute"'
    def execute(self) -> None:
        super().execute()
        pass
