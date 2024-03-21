# -*- coding: utf-8 -*-
# type: ignore

from .main import CreateClusterHandler

MODULE_NAME = "create_cluster"
HANDLER_CLASS = CreateClusterHandler
REQUIRES = []
AFTER = []
PREFLIGHT_REQUIRES = ["analyze_ceph"]
