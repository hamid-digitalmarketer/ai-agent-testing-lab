"""Unit tests for lab.integration."""

from __future__ import annotations

import json

import pytest
from lab.harness import AgentLoadError
from lab.integration import (
    default_thresholds,
    run_lab_eval,
    thresholds_from_json,
)

_DATASETS = "evaluation/datasets"


def test_run_lab_eval_passes_for_reliable(tmp_path):
    result = run_lab_eval(
        target_spec="fixtures:build_reliable",
        datasets_dir=_DATASETS,
        report_dir=tmp_path,
        reliability_runs=3,
    )
    assert result.passed is True
    assert result.target_name == "fixtures:build_reliable"
    assert result.metrics["factual_accuracy"] == 1.0
    assert (tmp_path / "metrics.json").exists()
    assert (tmp_path / "report.md").exists()
    assert (tmp_path / "dashboard.html").exists()


def test_run_lab_eval_fails_for_broken(tmp_path):
    result = run_lab_eval(
        target_spec="fixtures:build_broken",
        datasets_dir=_DATASETS,
        report_dir=tmp_path,
        reliability_runs=3,
    )
    assert result.passed is False
    assert result.metrics["tool_use_success"] == 0.0


def test_run_lab_eval_ci_summary(tmp_path, monkeypatch):
    summary = tmp_path / "step_summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    result = run_lab_eval(
        target_spec="fixtures:build_reliable",
        datasets_dir=_DATASETS,
        report_dir=tmp_path / "out",
        ci_summary=True,
        reliability_runs=2,
    )
    assert result.summary_path == str(summary)
    assert "Lab Evaluation Report" in summary.read_text(encoding="utf-8")


def test_run_lab_eval_bad_target_fails_cleanly(tmp_path):
    with pytest.raises(AgentLoadError):
        run_lab_eval(
            target_spec="no_such_module:build_agents",
            datasets_dir=_DATASETS,
            report_dir=tmp_path,
        )


def test_thresholds_from_json_none():
    assert thresholds_from_json(None) is None


def test_thresholds_from_json_file(tmp_path):
    path = tmp_path / "thresholds.json"
    path.write_text(json.dumps({"accuracy": 0.9, "reliability": 0.5}), encoding="utf-8")
    parsed = thresholds_from_json(path)
    assert parsed == {"accuracy": 0.9, "reliability": 0.5}


def test_thresholds_from_json_ignores_non_numbers(tmp_path):
    path = tmp_path / "thresholds.json"
    path.write_text(json.dumps({"accuracy": 0.9, "note": "hello"}), encoding="utf-8")
    assert thresholds_from_json(path) == {"accuracy": 0.9}


def test_thresholds_from_json_non_object(tmp_path):
    path = tmp_path / "thresholds.json"
    path.write_text("[1,2]", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON object"):
        thresholds_from_json(path)


def test_default_thresholds_copy():
    copied = default_thresholds()
    copied["accuracy"] = 0.1
    assert default_thresholds()["accuracy"] == 0.8
