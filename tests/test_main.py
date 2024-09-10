import sys
from typing import Any, Callable, Optional
import pytest
from _pytest.monkeypatch import MonkeyPatch
import yaml
from unittest.mock import MagicMock
import pytest_structlog

from argparse import Namespace

from rookify.__main__ import parse_args, main, sort_pickle_file
import rookify.yaml


# Test the arugment parser
def test_parse_args_dry_run() -> None:
    args = parse_args(["--dry-run"])
    expected = Namespace(dry_run_mode=True, read_pickle=None, show_progress=None)
    assert args == expected


def test_parse_args_read_pickle() -> None:
    args = parse_args(["--read-pickle"])
    expected = Namespace(dry_run_mode=False, read_pickle="all", show_progress=None)
    assert args == expected


def test_parse_args_both_flags() -> None:
    args = parse_args(["--dry-run", "--read-pickle"])
    expected = Namespace(dry_run_mode=True, read_pickle="all", show_progress=None)
    assert args == expected


def test_parse_args_show_progress() -> None:
    args = parse_args(["--show-progress"])
    expected = Namespace(dry_run_mode=False, read_pickle=None, show_progress="all")
    assert args == expected


# check: should it be possible to add all arguments?
def test_parse_args_both_dry_run_show_progress() -> None:
    args = parse_args(["--dry-run", "--read-pickle", "--show-progress"])
    expected = Namespace(dry_run_mode=True, read_pickle="all", show_progress="all")
    assert args == expected


def test_parse_args_all_dry_run_show_progress_read_pickle() -> None:
    args = parse_args(["--dry-run", "--show-progress"])
    expected = Namespace(dry_run_mode=True, read_pickle=None, show_progress="all")
    assert args == expected


def test_parse_args_no_flags() -> None:
    args = parse_args([])
    expected = Namespace(dry_run_mode=False, read_pickle=None, show_progress=None)
    assert args == expected


# Test the --read-pickle and --show-progress options


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
