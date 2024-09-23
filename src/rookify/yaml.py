# -*- coding: utf-8 -*-

import importlib.resources
import yamale
from pathlib import Path
from typing import Any, Dict

# Use Any instead importlib.resources.abc. Traversable for Python < 3.11
_config_schema_file: Any = Path("rookify", "config.schema.yaml")
for entry in importlib.resources.files("rookify").iterdir():
    if entry.name == "config.schema.yaml":
        _config_schema_file = entry


def load_config(path: str) -> Dict[str, Any]:
    schema = yamale.make_schema(_config_schema_file)
    data = yamale.make_data(path)

    yamale.validate(schema, data)

    assert isinstance(data[0][0], dict)
    return data[0][0]
