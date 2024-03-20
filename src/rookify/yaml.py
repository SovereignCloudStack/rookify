# -*- coding: utf-8 -*-

import yaml
from typing import Any, Dict


def load_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r") as file:
        data = yaml.safe_load(file)
        assert isinstance(data, dict)
        return data


def save_yaml(path: str, data: Dict[str, Any]) -> None:
    with open(path, "w") as file:
        yaml.safe_dump(data, file)
