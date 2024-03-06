# -*- coding: utf-8 -*-

import rookify.modules

from types import MappingProxyType
from .yaml import load_yaml, save_yaml

def main():
    try:
        config = load_yaml("config.yaml")
    except FileNotFoundError as err:
        raise SystemExit(f'Could not load config: {err}')
    preflight_modules, migration_modules = rookify.modules.load_modules(config['migration_modules'])

    module_data = dict()
    try:
        module_data.update(load_yaml(config['general']['module_data_file']))
    except FileNotFoundError:
        pass

    # Run preflight requirement modules
    for preflight_module in preflight_modules:
        handler = preflight_module.HANDLER_CLASS(config=MappingProxyType(config), data=MappingProxyType(module_data))
        result = handler.run()
        module_data[preflight_module.MODULE_NAME] = result

    # Run preflight checks and append handlers to list
    handlers = list()
    for migration_module in migration_modules:
        handler = migration_module.HANDLER_CLASS(config=MappingProxyType(config), data=MappingProxyType(module_data))
        handler.preflight_check()
        handlers.append((migration_module, handler))
    
    # Run migration modules
    for migration_module, handler in handlers:
        result = handler.run()
        module_data[migration_module.MODULE_NAME] = result

    save_yaml(config['general']['module_data_file'], module_data)

if __name__ == "__main__":
    main()
