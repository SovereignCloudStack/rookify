# -*- coding: utf-8 -*-

import yaml

def load_yaml(path: str) -> dict:
    with open(path, 'r') as file:
        return yaml.safe_load(file)

def save_yaml(path: str, data: dict) -> None:
    with open(path, 'w') as file:
        yaml.safe_dump(data, file)
