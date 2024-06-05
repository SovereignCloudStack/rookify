# -*- coding: utf-8 -*-

import kubernetes
from typing import Any, Callable, Dict, Optional


class K8s:
    def __init__(self, config: Dict[str, Any]):
        k8s_config = kubernetes.config.load_kube_config(config_file=config["config"])
        self.__client = kubernetes.client.ApiClient(k8s_config)
        self.__dynamic_client: Optional[kubernetes.dynamic.DynamicClient] = None

    @property
    def core_v1_api(self) -> kubernetes.client.CoreV1Api:
        return kubernetes.client.CoreV1Api(self.__client)

    @property
    def apps_v1_api(self) -> kubernetes.client.AppsV1Api:
        return kubernetes.client.AppsV1Api(self.__client)

    @property
    def node_v1_api(self) -> kubernetes.client.NodeV1Api:
        return kubernetes.client.NodeV1Api(self.__client)

    @property
    def custom_objects_api(self) -> kubernetes.client.CustomObjectsApi:
        return kubernetes.client.CustomObjectsApi(self.__client)

    @property
    def dynamic_client(self) -> kubernetes.dynamic.DynamicClient:
        if not self.__dynamic_client:
            self.__dynamic_client = kubernetes.dynamic.DynamicClient(self.__client)
        return self.__dynamic_client

    def crd_api(
        self, api_version: str, kind: str
    ) -> kubernetes.dynamic.resource.Resource:
        return self.dynamic_client.resources.get(api_version=api_version, kind=kind)

    def crd_api_apply(
        self, manifest: Dict[Any, Any]
    ) -> kubernetes.dynamic.resource.ResourceInstance:
        """
        This applies a manifest for custom CRDs
        See https://github.com/kubernetes-client/python/issues/1792 for more information
        :param manifest: Dict of the kubernetes manifest
        """
        api_version = manifest["apiVersion"]
        kind = manifest["kind"]
        resource_name = manifest["metadata"]["name"]
        namespace = manifest["metadata"]["namespace"]
        crd_api = self.crd_api(api_version=api_version, kind=kind)

        try:
            crd_api.get(namespace=namespace, name=resource_name)
            return crd_api.patch(
                body=manifest, content_type="application/merge-patch+json"
            )
        except kubernetes.dynamic.exceptions.NotFoundError:
            return crd_api.create(body=manifest, namespace=namespace)

    def watch_events(
        self,
        callback_func: Callable[[Any], Any],
        func: Callable[[Any], Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        watcher = kubernetes.watch.Watch()

        stream = watcher.stream(func, *args, **kwargs)

        try:
            for event in stream:
                try:
                    result = callback_func(event["object"])
                except StopIteration:
                    continue

                if result is not None:
                    return result
        finally:
            watcher.stop()
