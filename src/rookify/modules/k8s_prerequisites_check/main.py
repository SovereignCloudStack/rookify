# -*- coding: utf-8 -*-

from ..exception import ModuleException
from ..module import ModuleHandler


class K8sPrerequisitesCheckHandler(ModuleHandler):
    def preflight(self) -> None:
        self.logger.debug("K8sPrerequisitesCheck started validation")

        # We are only looking up labels here. This is a sanity check only without guarantee that the deployment found is operational or the Rook operator at all.
        deployments = self.k8s.apps_v1_api.list_deployment_for_all_namespaces(
            field_selector="metadata.name=rook-ceph-operator",
            label_selector="operator=rook",
        )

        if len(deployments.items) < 1:
            raise ModuleException("Rook operator not found")

        namespace = self._config["rook"]["cluster"]["namespace"]

        namespaces = [
            namespace.metadata.name
            for namespace in self.k8s.core_v1_api.list_namespace().items
        ]

        if namespace not in namespaces:
            raise ModuleException("Namespace {0} does not exist".format(namespace))

        nodes = self.k8s.core_v1_api.list_node().items

        for node in nodes:
            node_labels = node.metadata.labels

            for label in [
                self.k8s.mds_placement_label,
                self.k8s.mgr_placement_label,
                self.k8s.mon_placement_label,
                self.k8s.osd_placement_label,
                self.k8s.rgw_placement_label,
            ]:
                if label in node_labels and node_labels[label] == "enabled":
                    raise ModuleException(
                        "Label {0} is set on node {1}".format(label, node.metadata.name)
                    )
        self.logger.info("K8sPrerequisitesCheck completed")
