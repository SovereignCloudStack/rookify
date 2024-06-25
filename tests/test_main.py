import sys
from typing import Callable, Optional
import pytest
from _pytest.monkeypatch import MonkeyPatch
import yaml
from unittest.mock import MagicMock
import pytest_structlog

from argparse import Namespace

from rookify.__main__ import parse_args, main
import rookify.yaml


# Test the arugment parser
def test_parse_args_dry_run() -> None:
    args = parse_args(["--dry-run"])
    expected = Namespace(dry_run_mode=True, show_progress=False)
    assert args == expected


def test_parse_args_show_progress() -> None:
    args = parse_args(["--show"])
    expected = Namespace(dry_run_mode=False, show_progress=True)
    assert args == expected


def test_parse_args_both_flags() -> None:
    args = parse_args(["--dry-run", "--show"])
    expected = Namespace(dry_run_mode=True, show_progress=True)
    assert args == expected


def test_parse_args_no_flags() -> None:
    args = parse_args([])
    expected = Namespace(dry_run_mode=False, show_progress=False)
    assert args == expected


# Test the --show option


@pytest.fixture  # type: ignore
def mock_load_config(monkeypatch: MonkeyPatch) -> Callable[[Optional[str]], MagicMock]:
    def _mock_load_config(pickle_file: Optional[str] = None) -> MagicMock:
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
    mock_states_data = {"mock_key": "mock_value"}

    # Mock load_pickler function
    mock = MagicMock(return_value=mock_states_data)
    monkeypatch.setattr(rookify.__main__, "load_pickler", mock)

    return mock


def test_main_show_progress(
    mock_load_config: Callable[[Optional[str]], MagicMock],
    mock_load_pickler: MonkeyPatch,
    monkeypatch: MonkeyPatch,
    log: pytest_structlog.StructuredLogCapture,
) -> None:
    # Load mock.pickle as a configuration file
    mock_load_config("mock.pickle")

    # Mock sys.argv to simulate command-line arguments
    monkeypatch.setattr(sys, "argv", ["main_script.py", "--show", "--dry-run"])

    # Run main()
    main()

    # Verify logging messages
    assert log.has("Pickle file set: mock.pickle")
    assert log.has(
        "Current state as retrieved from pickle-file: {'mock_key': 'mock_value'}"
    )


def test_main_no_pickle_file(
    mock_load_config: Callable[[Optional[str]], MagicMock],
    mock_load_pickler: MonkeyPatch,
    monkeypatch: MonkeyPatch,
    log: pytest_structlog.StructuredLogCapture,
) -> None:
    # Load a configuration without pickle: This should load the default data.pickle file if it is available
    mock_load_config(None)

    # Mock sys.argv to simulate command-line arguments
    monkeypatch.setattr(sys, "argv", ["main_script.py", "--show", "--dry-run"])

    # Run main()
    main()

    # Assertions
    assert log.has("No pickle file was set in the configuration.")
