# -*- coding: utf-8 -*-

import os
import rookify.modules

from types import MappingProxyType
from .yaml import load_config, load_module_data, save_module_data


def main() -> None:
    try:
        config = load_config("config.yaml")
    except FileNotFoundError as err:
        raise SystemExit(f"Could not load config: {err}")
    preflight_modules, migration_modules = rookify.modules.load_modules(
        config["migration_modules"]
    )

    module_data = dict()
    try:
        module_data.update(load_module_data(config["general"]["module_data_file"]))
    except FileNotFoundError:
        pass

    # Get absolute path of the rookify instance
    rookify_path = os.path.dirname(__file__)

    # Run preflight requirement modules
    for preflight_module in preflight_modules:
        module_path = os.path.join(
            rookify_path, "modules", preflight_module.MODULE_NAME
        )
        handler = preflight_module.HANDLER_CLASS(
            config=MappingProxyType(config),
            data=MappingProxyType(module_data),
            module_path=module_path,
        )
        result = handler.run()
        module_data[preflight_module.MODULE_NAME] = result

    # Run preflight and append handlers to list
    handlers = list()
    for migration_module in migration_modules:
        module_path = os.path.join(
            rookify_path, "modules", migration_module.MODULE_NAME
        )
        handler = migration_module.HANDLER_CLASS(
            config=MappingProxyType(config),
            data=MappingProxyType(module_data),
            module_path=module_path,
        )
        handler.preflight()
        handlers.append((migration_module, handler))

    # Run migration modules
    for migration_module, handler in handlers:
        result = handler.run()
        module_data[migration_module.MODULE_NAME] = result

    save_module_data(config["general"]["module_data_file"], module_data)


if __name__ == "__main__":
    main()
