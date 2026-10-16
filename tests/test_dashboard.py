"""Unit tests for lab.dashboard."""

from __future__ import annotations

from lab.dashboard import render_dashboard
from lab.harness import LabReport


def _report(metrics=None):
    return LabReport(
        target_name="demo.target",
        metrics=metrics
        or {
            "accuracy": 0.95,
            "cost_control": 1.0,
            "reliability": 0.4,
        },
        details={"cost_control": "measured $0.0000 (cap $0.00)"},
        dataset_summary={"factual_accuracy": 3},
        agent_names=["reliable", "broken"],
    )


def test_render_dashboard_contains_title_and_metrics():
    html = render_dashboard(_report())
    assert "Lab Evaluation Report" in html
    assert "demo.target" in html
    assert "accuracy" in html
    assert "reliability" in html
    assert "PASS" in html


def test_render_dashboard_shows_fail():
    html = render_dashboard(_report({"reliability": 0.4, "cost_control": 1.0}))
    assert "FAIL" in html
    assert "bad" in html


def test_render_dashboard_escapes_target():
    html = render_dashboard(_report())
    assert "demo.target" in html


def test_render_dashboard_empty_details_ok():
    report = LabReport(target_name="t", metrics={"accuracy": 0.5})
    html = render_dashboard(report)
    assert "Metrics" in html
