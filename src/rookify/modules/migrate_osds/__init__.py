# -*- coding: utf-8 -*-
# type: ignore

from .main import MigrateOSDsHandler

MODULE_NAME = "migrate_osds"
HANDLER_CLASS = MigrateOSDsHandler
REQUIRES = []
AFTER = ["migrate_monitors"]
PREFLIGHT_REQUIRES = ["analyze_ceph"]
