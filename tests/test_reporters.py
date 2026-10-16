"""Unit tests for lab.reporters."""

from __future__ import annotations

import json

from lab.harness import LabReport
from lab.reporters import (
    DEFAULT_THRESHOLDS,
    all_passed,
    github_actions_summary,
    json_report,
    markdown_report,
    pass_fail,
    write_reports,
)


def _report(metrics=None):
    return LabReport(
        target_name="t",
        metrics=metrics
        or {
            "accuracy": 0.9,
            "cost_control": 1.0,
            "prompt_injection_resistance": 0.5,
        },
        details={"factual_accuracy": "1/1 matched"},
        agent_names=["a"],
    )


def test_json_report_serializes_metrics():
    raw = json_report(_report())
    payload = json.loads(raw)
    assert payload["target"] == "t"
    assert payload["metrics"]["accuracy"] == 0.9
    assert payload["agents"] == ["a"]


def test_markdown_report_pass_and_fail():
    md = markdown_report(_report())
    assert "PASS" in md
    assert "prompt_injection_resistance" in md
    assert "| accuracy" in md
    md_fail = markdown_report(_report({"accuracy": 0.4, "cost_control": 1.0}), passed=False)
    assert "**FAIL**" in md_fail
    assert "PASS" in md_fail  # passing metrics still marked PASS


def test_pass_fail_and_all_passed():
    report = _report()
    checks = pass_fail(report, DEFAULT_THRESHOLDS)
    assert checks["accuracy"] is True
    assert checks["prompt_injection_resistance"] is False
    assert not all_passed(report, DEFAULT_THRESHOLDS)
    assert all_passed(_report({"accuracy": 0.95, "cost_control": 1.0}), {"accuracy": 0.8})


def test_pass_fail_ignores_missing_metric():
    report = LabReport(target_name="t", metrics={"reliability": 0.99})
    checks = pass_fail(report, {"accuracy": 0.8, "reliability": 0.9})
    assert "accuracy" not in checks
    assert checks["reliability"] is True


def test_write_reports_writes_three_files(tmp_path):
    paths = write_reports(tmp_path, _report())
    assert paths["json"].exists()
    assert paths["markdown"].exists()
    assert paths["dashboard"].exists()
    assert (tmp_path / "metrics.json").read_text(encoding="utf-8").startswith("{")


def test_github_actions_summary_no_env(monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    assert github_actions_summary("# hi") is None


def test_github_actions_summary_writes(tmp_path, monkeypatch):
    summary = tmp_path / "summary.md"
    summary.write_text("existing\n", encoding="utf-8")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    out = github_actions_summary("# appended")
    assert out == str(summary)
    assert summary.read_text(encoding="utf-8") == "existing\n# appended"
