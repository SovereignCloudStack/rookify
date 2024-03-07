# -*- coding: utf-8 -*-

from .main import MigrateOSDsHandler

MODULE_NAME = "migrate_osds"
HANDLER_CLASS = MigrateOSDsHandler
REQUIRES = []
AFTER = ["migrate_monitors"]
PREFLIGHT_REQUIRES = ["analyze_ceph"]
