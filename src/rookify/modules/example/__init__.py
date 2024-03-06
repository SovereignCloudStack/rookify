# -*- coding: utf-8 -*-

from .main import ExampleHandler

MODULE_NAME = 'example' # Name of the module
HANDLER_CLASS = ExampleHandler # Define the handler class for this module
REQUIRES = [] # A list of modules that are required to run before this module. Modules in this list will be imported, even if they are not configured
AFTER = ['migrate_monitors'] # A list of modules that should be run before this module, if they are defined in config
PREFLIGHT_REQUIRES = ['analyze_ceph'] # A list of modules that are required to run the preflight_check of this module. Modules in this list will be imported and run in preflight stage.