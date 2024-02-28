from .main import ExampleHandler

HANDLER_CLASS = ExampleHandler # Define the handler class for this module
RUN_IN_PREFLIGHT = False # This executes the run method during preflight checks. This is neccessary for analyze modules.
REQUIRES = ['analyze_ceph'] # A list of modules that are required to run before this module. Modules in this list will be imported, even if they are not configured
AFTER = ['migrate_monitors'] # A list of modules that should be run before this module, if they are defined in config