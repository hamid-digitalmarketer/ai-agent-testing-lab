"""Unit tests for the lab-eval CLI entry point."""

from __future__ import annotations

import pytest
from lab.cli import build_parser, main

_DATASETS = "evaluation/datasets"


def test_build_parser_requires_target():
    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args(["--datasets", _DATASETS])
    assert exc.value.code == 2


def test_main_passes_for_reliable(tmp_path):
    code = main(
        [
            "--target",
            "fixtures:build_reliable",
            "--datasets",
            _DATASETS,
            "--report-dir",
            str(tmp_path),
            "--reliability-runs",
            "2",
        ]
    )
    assert code == 0
    assert (tmp_path / "metrics.json").exists()


def test_main_fails_for_broken(tmp_path):
    code = main(
        [
            "--target",
            "fixtures:build_broken",
            "--datasets",
            _DATASETS,
            "--report-dir",
            str(tmp_path),
            "--reliability-runs",
            "2",
        ]
    )
    assert code == 1


def test_main_error_path(tmp_path, capsys):
    code = main(
        [
            "--target",
            "no_such_module:build_agents",
            "--datasets",
            _DATASETS,
            "--report-dir",
            str(tmp_path),
        ]
    )
    assert code == 2
    assert "lab-eval failed" in capsys.readouterr().err
