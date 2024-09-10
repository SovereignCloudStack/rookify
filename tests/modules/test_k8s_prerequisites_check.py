import unittest
from unittest.mock import Mock

from rookify.modules.exception import ModuleException
from kubernetes.client import V1Namespace, V1ObjectMeta, V1NamespaceList
from typing import Any, Dict, List
from ..mock_k8s_prerequisite_check import MockK8sPrerequisitesCheckHandler


# Note: currently this test works with pytest but not with unittest, which is not able to import needed classes
class TestK8sPrerequisitesCheckHandler(unittest.TestCase):
    def setUp(self) -> None:
        # Mock configuration
        self.config = {"rook": {"cluster": {"namespace": "test-namespace"}}}
        # No response option
        self.empty_response = False

    def _request_callback(
        self, method: str, *args: List[Any], **kwargs: Dict[Any, Any]
    ) -> Any:
        if method == "apps_v1_api.list_deployment_for_all_namespaces":
            if self.empty_response is True:
                return V1DeploymentList([])
            return V1DeploymentList(["apple", "banana", "cherry"])
        if method == "core_v1_api.list_namespace":
            return self._mock_v1namespacelist()

    def _mock_v1namespacelist(self) -> Any:
        # Create a list of Kubernetes V1Namespace objects
        namespaces = [
            V1Namespace(metadata=V1ObjectMeta(name="default")),
            V1Namespace(metadata=V1ObjectMeta(name="kube-system")),
            V1Namespace(metadata=V1ObjectMeta(name="test-namespace")),
        ]
        return V1NamespaceList(items=namespaces)

    def test_namespaces(self) -> None:
        # Instantiate K8sPrerequisitesCheckHandler with the mock ModuleHandler
        handler_instance = MockK8sPrerequisitesCheckHandler(
            self._request_callback, Mock(), self.config
        )
        # Set the k8s attribute to the mock_k8s instance
        handler_instance.preflight()

    def test_list_deployment_for_all_namespaces_fails(self) -> None:
        # Set no response
        self.empty_response = True

        # Instantiate K8sPrerequisitesCheckHandler with the mock ModuleHandler
        handler_instance = MockK8sPrerequisitesCheckHandler(
            self._request_callback, Mock(), self.config
        )

        # Call the preflight method to run the test
        with self.assertRaises(ModuleException):
            handler_instance.preflight()

    def test_namespaces_fails(self) -> None:
        # Instantiate K8sPrerequisitesCheckHandler with the mock ModuleHandler
        handler_instance = MockK8sPrerequisitesCheckHandler(
            self._request_callback, Mock(), self.config
        )

        # Modify the config to have a different namespace than what is expected
        handler_instance._config["rook"]["cluster"]["namespace"] = "wrong-namespace"
        # Call the preflight method to run the test
        with self.assertRaises(ModuleException):
            handler_instance.preflight()


# Create a Mock respons for the V1DeploymentList object
class V1DeploymentList:
    def __init__(self, items: List[str]) -> None:
        self.items = items
