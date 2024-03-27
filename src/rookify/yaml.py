# -*- coding: utf-8 -*-

import yamale
import yaml
from importlib import resources
from pathlib import Path
from typing import Any, Dict


_schema_file = Path("rookify", "config.schema.yaml")
for entry in resources.files("rookify").iterdir():
    if entry.name == "config.schema.yaml":
        _schema_file = entry


def load_yaml(path: str) -> Dict[str, Any]:
    schema = yamale.make_schema(_schema_file)
    data = yamale.make_data(path)

    yamale.validate(schema, data)

    assert isinstance(data[0][0], dict)
    return data[0][0]


def save_yaml(path: str, data: Dict[str, Any]) -> None:
    with open(path, "w") as file:
        yaml.safe_dump(data, file)
