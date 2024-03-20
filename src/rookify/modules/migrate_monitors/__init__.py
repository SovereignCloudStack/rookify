# -*- coding: utf-8 -*-
# type: ignore

from .main import MigrateMonitorsHandler

MODULE_NAME = "migrate_monitors"
HANDLER_CLASS = MigrateMonitorsHandler
REQUIRES = []
AFTER = []
PREFLIGHT_REQUIRES = ["analyze_ceph"]
