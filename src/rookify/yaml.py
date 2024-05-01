# -*- coding: utf-8 -*-

import importlib.resources
import importlib.resources.abc
import yamale
import yaml
from pathlib import Path
from typing import Any, Dict


_config_schema_file: Path | importlib.resources.abc.Traversable = Path(
    "rookify", "config.schema.yaml"
)
for entry in importlib.resources.files("rookify").iterdir():
    if entry.name == "config.schema.yaml":
        _config_schema_file = entry


def load_config(path: str) -> Dict[str, Any]:
    schema = yamale.make_schema(_config_schema_file)
    data = yamale.make_data(path)

    yamale.validate(schema, data)

    assert isinstance(data[0][0], dict)
    return data[0][0]


def load_module_data(path: str) -> Dict[str, Any]:
    with open(path, "r") as file:
        data = yaml.safe_load(file)
        assert isinstance(data, dict)
        return data


def save_module_data(path: str, data: Dict[str, Any]) -> None:
    with open(path, "w") as file:
        yaml.safe_dump(data, file)
