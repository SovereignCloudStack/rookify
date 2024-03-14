# -*- coding: utf-8 -*-

"""
Copyright (c) Sovereign Cloud Stack Developers

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.

You may obtain a copy of the License at
 http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from typing import Dict, Any

try:
    from setuptools import find_packages, setup
except ImportError:
    from distutils import find_packages, setup  # type: ignore[attr-defined, unused-ignore]


def get_version() -> str:
    """
    Returns the version currently in development.

    :return: (str) Version string
    :since:  v0.0.1
    """

    return "v0.0.1"


#

_setup: Dict[str, Any] = {
    "version": get_version()[1:],
    "data_files": [("docs", ["LICENSE", "README.md"])],
    "test_suite": "tests",
}

_setup["package_dir"] = {"": "src"}
_setup["packages"] = find_packages("src")

setup(**_setup)
