# -*- coding: utf-8 -*-
# type: ignore

from .main import CreateConfigMapHandler

MODULE_NAME = "create_configmap"
HANDLER_CLASS = CreateConfigMapHandler
REQUIRES = []
AFTER = []
PREFLIGHT_REQUIRES = ["analyze_ceph"]
