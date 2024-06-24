from argparse import Namespace
from rookify.__main__ import parse_args


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
