#!/usr/bin/env python3

import modules
import yaml
from types import MappingProxyType

def load_yaml(path: str) -> dict:
    with open(path, 'r') as file:
        return yaml.safe_load(file)

def save_yaml(path: str, data: dict) -> None:
    with open(path, 'w') as file:
        yaml.safe_dump(data, file)

def main():

    try:
        config = load_yaml("config.yaml")
    except FileNotFoundError as err:
        raise SystemExit(f'Could not load config: {err}')
    migration_modules = modules.load_modules(config['migration_modules'])

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
            module_data[module.__name__] = result
        else:
            handlers.append((module, handler))
    
    # Do preflight check of all other handlers
    for module, handler in handlers:
        handler.preflight_check()

    # Run handlers
    for module, handler in handlers:
        result = handler.run()
        module_data[module.__name__] = result
        
    save_yaml(config['general']['module_data_file'], module_data)
    
if __name__ == "__main__":
    main()