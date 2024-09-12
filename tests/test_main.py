import sys
from typing import Any, Callable, Optional, List, Tuple
import pytest
from _pytest.monkeypatch import MonkeyPatch
import yaml
from unittest.mock import MagicMock
import pytest_structlog

import argparse

from rookify.__main__ import parse_args, main, sort_pickle_file
import rookify.yaml

#
# These tests test the src/rookify/__main__.py
#
# Run all tests: .venv/bin/python -m pytest tests/
# Run one test with output: .venv/bin/python -m pytest tests/ -k name_of_test -s
#


# Test the arugment parser

# Custom type for argument parser tests
TestCase = Tuple[List[str], argparse.Namespace]

# fmt: off
test_cases: List[TestCase] = [
    (["--dry-run"], argparse.Namespace(dry_run_mode=True, list_modules=False, read_pickle=None, show_progress=None)),
    (["--read-pickle"], argparse.Namespace(dry_run_mode=False, list_modules=False, read_pickle="all", show_progress=None)),
    (["--show-progress"], argparse.Namespace(dry_run_mode=False, list_modules=False, read_pickle=None, show_progress="all")),
    (["--show-progress", "ceph-analyze"], argparse.Namespace(dry_run_mode=False, list_modules=False, read_pickle=None, show_progress="ceph-analyze")),
    (["--dry-run", "--read-pickle"], argparse.Namespace(dry_run_mode=True, list_modules=False, read_pickle="all", show_progress=None)),
    (["--dry-run", "--show-progress"], argparse.Namespace(dry_run_mode=True, list_modules=False, read_pickle=None, show_progress="all")),
    (["--dry-run", "--show-progress", "--read-pickle"], argparse.Namespace(dry_run_mode=True, list_modules=False, read_pickle="all", show_progress="all")),
    ([], argparse.Namespace(dry_run_mode=False, list_modules=False, read_pickle=None, show_progress=None)),
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


@pytest.fixture  # type: ignore
def mock_load_config(monkeypatch: MonkeyPatch) -> Callable[[Optional[Any]], MagicMock]:
    def _mock_load_config(pickle_file: Optional[Any] = None) -> MagicMock:
        # Mock the configuration data
        # Load config.example.yaml
        with open("config.example.yaml", "r") as file:
            config_data = yaml.safe_load(file)

        config_data["general"]["machine_pickle_file"] = pickle_file

        # Mock load_config function
        mock = MagicMock(return_value=config_data)
        monkeypatch.setattr(rookify.__main__, "load_config", mock)

        return mock

    return _mock_load_config


@pytest.fixture  # type: ignore
def mock_load_pickler(monkeypatch: MonkeyPatch) -> MagicMock:
    # Mock states_data from pickle file
    mock_states_data = {"teststuff": {"data": {"mock_key": "mock_value"}}}

    # Mock load_pickler function
    mock = MagicMock(return_value=mock_states_data)
    monkeypatch.setattr(rookify.__main__, "load_pickler", mock)

    return mock


def test_main_read_pickle(
    mock_load_config: Callable[[Optional[Any]], MagicMock],
    mock_load_pickler: MonkeyPatch,
    monkeypatch: MonkeyPatch,
    log: pytest_structlog.StructuredLogCapture,
) -> None:
    # Load example config with mock.pickle as pickle file
    mock_load_config("mock.pickle")

    # Mock sys.argv to simulate command-line arguments
    monkeypatch.setattr(sys, "argv", ["main_script.py", "--read-pickle", "--dry-run"])

    # Run main()
    main()

    # Verify logging messages
    expected_log_message = (
        'Current state as retrieved from pickle-file: \n "all": '
        "{\n"
        '    "mock_key": "mock_value"\n'
        "}"
    )
    assert log.has("Pickle file set: mock.pickle", level="info")
    assert log.has(expected_log_message, level="info")


def test_main_no_pickle_file(
    mock_load_config: Callable[[Optional[str]], MagicMock],
    mock_load_pickler: MonkeyPatch,
    monkeypatch: MonkeyPatch,
    log: pytest_structlog.StructuredLogCapture,
) -> None:
    # Load a configuration without pickle: This should load the default data.pickle file if it is available
    mock_load_config(None)

    # Mock sys.argv to simulate command-line arguments
    monkeypatch.setattr(sys, "argv", ["main_script.py", "--read-pickle", "--dry-run"])

    # Run main()
    main()

    # Assertions
    assert log.has("No pickle file was set in the configuration.")


def test_sort_pickle_file() -> None:
    #  Prepare unsorted data
    unsorted_states_data = getUnsortedData()

    # Expected keys order
    expected_order = ["device", "fs", "mon", "node", "osd", "ssh"]

    # Run sort_pickle_file
    sorted_states_data = sort_pickle_file(unsorted_states_data)

    # Assert that order is correct
    sorted_states_data_keys = list(sorted_states_data.keys())

    assert expected_order == sorted_states_data_keys


def getUnsortedData() -> Any:
    unsorted_states_data = {
        "preflighttestdata": {
            "data": {
                "mon": {
                    "dump": {"epoch": 1},
                    "mons": [{"rank": 0}],
                    "quorum": [0, 1, 2],
                },
                "fs": {"dump": {"epoch": 1}},
                "device": {"ls": ["devid", 1]},
                "osd": {
                    "dump": [{"epoch": 138}],
                    "osds": [{"osd": 0}],
                    "osd_xinfo": [{"osd": 0}],
                },
                "node": {
                    "ls": {
                        "mon": {
                            "test-node-0": ["test-node-0"],
                            "test-node-1": ["test-node-1"],
                            "test-node-2": ["test-node-2"],
                        },
                        "osd": {
                            "test-node-0": [2, 3],
                            "test-node-1": [0, 5],
                            "test-node-2": [1, 4],
                        },
                        "mds": {
                            "test-node-0": ["test-node-0"],
                            "test-node-1": ["test-node-1"],
                            "test-node-2": ["test-node-2"],
                        },
                        "mgr": {
                            "test-node-0": ["test-node-0"],
                            "test-node-1": ["test-node-1"],
                            "test-node-2": ["test-node-2"],
                        },
                    }
                },
                "ssh": {
                    "osd": {
                        "test-node-0": {
                            "devices": ["/dev/ceph-bla-1", "/dev/ceph-bla-2"]
                        },
                        "test-node-1": {
                            "devices": ["/dev/ceph-bla-3", "/dev/ceph-bla-4"]
                        },
                        "test-node-2": {
                            "devices": ["/dev/ceph-bla-5", "/dev/ceph-bla-6"]
                        },
                    }
                },
            }
        }
    }

    return unsorted_states_data


# Custom Type for Logger of CLI
TestCaseLogger = Tuple[List[str], str, str]

# fmt: off
logger_test_cases: List[TestCaseLogger] = [
    (["--show-progress", "analyze_ceph"], "Show progress of the analyze_ceph module", "info"),
    (["--dry-run", "--show-progress", "analyze_ceph"], "Show progress of the analyze_ceph module", "info"),
    (["--show-progress"], "Show progress of all modules", "info"),
    (["--dry-run", "--show-progress"], "Show progress of all modules", "info"),
    (["--show-progress"], "Analyze ceph has been run", "info")
]
# fmt: on


@pytest.mark.parametrize(
    "args_list, expected_log_message, expected_level",
    logger_test_cases,
)  # type: ignore
def test_show_progress_logs(
    mock_load_config: Callable[[Optional[Any]], MagicMock],
    monkeypatch: MonkeyPatch,
    log: pytest_structlog.StructuredLogCapture,
    args_list: List[str],
    expected_log_message: str,
    expected_level: str,
) -> None:
    # Load example config with mock.pickle as pickle file
    mock_load_config("mock.pickle")

    # Mock sys.argv to simulate command-line arguments
    args_list.insert(0, "main_script.py")
    monkeypatch.setattr(sys, "argv", args_list)

    # Run main()
    main()

    # Assertions
    assert log.has(expected_log_message, level=expected_level)
