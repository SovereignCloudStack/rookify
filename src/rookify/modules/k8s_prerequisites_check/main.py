# -*- coding: utf-8 -*-

from ..module import ModuleException, ModuleHandler


class K8sPrerequisitesCheckHandler(ModuleHandler):
    def preflight(self) -> None:
        namespace = self._config["rook"]["cluster"]["namespace"]

        namespaces = [
            namespace.metadata.name
            for namespace in self.k8s.core_v1_api.list_namespace().items
        ]

        if namespace not in namespaces:
            raise ModuleException("Namespace {0} does not exist".format(namespace))
