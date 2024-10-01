import argparse
import pytest
from rookify.__main__ import parse_args
from typing import List, Tuple

#
# These tests test the src/rookify/__main__.py
#
# Run all tests: .venv/bin/python -m pytest tests/
# Run one test with output: .venv/bin/python -m pytest tests/ -k name_of_test -s
#

# Test the argument parser

# Custom type for argument parser tests
TestCase = Tuple[List[str], argparse.Namespace]

# fmt: off
test_cases: List[TestCase] = [
    (["--migrate"], argparse.Namespace(dry_run_mode=False, show_states=False, execution_mode=True)),
    (["--migrate", "--dry-run"], argparse.Namespace(dry_run_mode=True, show_states=False, execution_mode=True)),
    (["--dry-run"], argparse.Namespace(dry_run_mode=True, show_states=False, execution_mode=False)),
    (["--show-states"], argparse.Namespace(dry_run_mode=False, show_states=True, execution_mode=False)),
    (["--dry-run", "--show-states"], argparse.Namespace(dry_run_mode=True, show_states=True, execution_mode=False)),
    ([], argparse.Namespace(dry_run_mode=True, show_states=False, execution_mode=False)),
]
# fmt: on


@pytest.mark.parametrize(
    "args_list, expected_namespace",
    test_cases,
)  # type: ignore
def test_parse_args(
    args_list: List[str], expected_namespace: argparse.Namespace
) -> None:
    args = parse_args(args_list)
    assert args == expected_namespace
