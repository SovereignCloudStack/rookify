# -*- coding: utf-8 -*-

from .main import MigrateMonitorsHandler

MODULE_NAME = 'migrate_monitors'
HANDLER_CLASS = MigrateMonitorsHandler
RUN_IN_PREFLIGHT = False
REQUIRES = ['analyze_ceph']
AFTER = []
