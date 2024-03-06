# -*- coding: utf-8 -*-

import rookify.modules

from types import MappingProxyType
from .yaml import load_yaml, save_yaml

def main():
    try:
        config = load_yaml("config.yaml")
    except FileNotFoundError as err:
        raise SystemExit(f'Could not load config: {err}')
    migration_modules = rookify.modules.load_modules(config['migration_modules'])

    module_data = dict()
    try:
        module_data.update(load_yaml(config['general']['module_data_file']))
    except FileNotFoundError:
        pass

    # Get a list of handlers and run handlers if they should be run in preflight
    handlers = list()
    for module in migration_modules:
        handler = module.HANDLER_CLASS(config=MappingProxyType(config), data=MappingProxyType(module_data))
        if module.RUN_IN_PREFLIGHT:
            handler.preflight_check()
            result = handler.run()
            module_data[module.MODULE_NAME] = result
        else:
            handlers.append((module, handler))

    # Do preflight check of all other handlers
    for module, handler in handlers:
        handler.preflight_check()

    # Run handlers
    for module, handler in handlers:
        result = handler.run()
        module_data[module.MODULE_NAME] = result

    save_yaml(config['general']['module_data_file'], module_data)

if __name__ == "__main__":
    main()
