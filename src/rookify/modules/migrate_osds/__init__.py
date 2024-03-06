# -*- coding: utf-8 -*-

from .main import MigrateOSDsHandler

MODULE_NAME = 'migrate_osds'
HANDLER_CLASS = MigrateOSDsHandler
RUN_IN_PREFLIGHT = False
REQUIRES = ['analyze_ceph']
AFTER = ['migrate_monitors']
