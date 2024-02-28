from .main import MigrateMonitorsHandler

HANDLER_CLASS = MigrateMonitorsHandler
RUN_IN_PREFLIGHT = False
REQUIRES = ['analyze_ceph']
AFTER = []