"""Metrics reporters: JSON, Markdown, GitHub Actions step summary.

Reporters turn a ``LabReport`` into artifacts that humans read (Markdown,
HTML dashboard) and machines consume (JSON). ``write_reports`` writes all of
them into a report directory and returns the produced paths.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from lab.harness import LabReport

# Default pass thresholds for the lab's own CI and for downstream repos.
DEFAULT_THRESHOLDS: dict[str, float] = {
    "accuracy": 0.8,
    "precision": 0.8,
    "recall": 0.8,
    "f1": 0.8,
    "calibration": 0.7,
    "factual_accuracy": 0.8,
    "tool_use_success": 0.8,
    "recommendation_quality": 0.8,
    "prompt_injection_resistance": 0.9,
    "cost_control": 1.0,
    "latency_budget": 1.0,
    "reliability": 0.9,
}


def pass_fail(report: LabReport, thresholds: dict[str, float] | None = None) -> dict[str, bool]:
    """Compare every metric against its threshold; missing threshold = pass."""
    thresholds = thresholds or DEFAULT_THRESHOLDS
    return {
        metric: report.score(metric) >= threshold
        for metric, threshold in thresholds.items()
        if metric in report.metrics
    }


def all_passed(report: LabReport, thresholds: dict[str, float] | None = None) -> bool:
    """True when every thresholded metric passes."""
    return all(pass_fail(report, thresholds).values())


def json_report(report: LabReport) -> str:
    """Serialize the report to machine-readable JSON."""
    payload: dict[str, Any] = {
        "target": report.target_name,
        "generated_at": report.generated_at,
        "agents": report.agent_names,
        "metrics": report.metrics,
        "details": report.details,
        "dataset_summary": report.dataset_summary,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def markdown_report(
    report: LabReport,
    thresholds: dict[str, float] | None = None,
    *,
    passed: bool | None = None,
) -> str:
    """Render a human-readable Markdown evaluation summary."""
    thresholds = thresholds or DEFAULT_THRESHOLDS
    verdict = passed if passed is not None else all_passed(report, thresholds)
    lines = [
        f"# Lab Evaluation Report: {report.target_name}",
        "",
        f"- Generated: {report.generated_at}",
        f"- Agents under test: {', '.join(report.agent_names) or 'none'}",
        f"- Overall: {'**PASS**' if verdict else '**FAIL**'}",
        "",
        "## Metrics",
        "",
        "| Metric | Score | Threshold | Status |",
        "| --- | ---: | ---: | --- |",
    ]
    for metric in sorted(report.metrics):
        score = report.metrics[metric]
        threshold = thresholds.get(metric)
        status = "PASS" if threshold is None or score >= threshold else "FAIL"
        th = f"{threshold:.2f}" if threshold is not None else "-"
        lines.append(f"| {metric} | {score:.3f} | {th} | {status} |")
    if report.details:
        lines.extend(["", "## Details", ""])
        for key, detail in sorted(report.details.items()):
            lines.append(f"- **{key}**: {detail}")
    return "\n".join(lines) + "\n"


def write_reports(
    report_dir: str | Path,
    report: LabReport,
    thresholds: dict[str, float] | None = None,
) -> dict[str, Path]:
    """Write metrics.json, report.md, and dashboard.html; return paths."""
    out = Path(report_dir)
    out.mkdir(parents=True, exist_ok=True)
    passed = all_passed(report, thresholds)

    json_path = out / "metrics.json"
    json_path.write_text(json_report(report), encoding="utf-8")

    md_path = out / "report.md"
    md_path.write_text(markdown_report(report, thresholds, passed=passed), encoding="utf-8")

    from lab.dashboard import render_dashboard

    dashboard_path = out / "dashboard.html"
    dashboard_path.write_text(render_dashboard(report), encoding="utf-8")

    return {"json": json_path, "markdown": md_path, "dashboard": dashboard_path}


def github_actions_summary(markdown: str) -> str | None:
    """Append the report to ``$GITHUB_STEP_SUMMARY`` when present in CI.

    Returns the summary path when it was written, else None.
    """
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return None
    with open(summary_path, "a", encoding="utf-8") as fh:
        fh.write(markdown)
    return summary_path
