"""CI integration helpers for the lab.

``run_lab_eval`` is the single entry point that downstream repositories call
from their own GitHub Actions (via the checked-out ``integration/run_lab_eval.py``
script) and that the lab itself uses in ``lab.cli``. It:

1. loads the target repo's agents through an import spec,
2. evaluates them against the lab's seven labeled datasets,
3. writes ``metrics.json`` / ``report.md`` / ``dashboard.html``,
4. optionally appends the Markdown report to ``$GITHUB_STEP_SUMMARY``,
5. exits non-zero when any threshold is missed, so CI fails loudly.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from lab.datasets import load_datasets
from lab.harness import TargetLoader, TestHarness
from lab.reporters import (
    DEFAULT_THRESHOLDS,
    all_passed,
    github_actions_summary,
    markdown_report,
    write_reports,
)


@dataclass
class LabEvalResult:
    """Outcome of one ``run_lab_eval`` execution."""

    target_name: str
    metrics: dict[str, float]
    report_paths: dict[str, Path]
    passed: bool
    summary_path: str | None = None


def run_lab_eval(
    *,
    target_spec: str,
    datasets_dir: str | Path,
    report_dir: str | Path,
    thresholds: dict[str, float] | None = None,
    write_dashboard: bool = True,
    ci_summary: bool = False,
    reliability_runs: int = 6,
) -> LabEvalResult:
    """Evaluate an installed target repo and emit CI artifacts."""
    datasets = load_datasets(datasets_dir)
    factory = TargetLoader.from_import(target_spec)
    harness = TestHarness(factory, datasets, reliability_runs=reliability_runs)
    report = harness.evaluate(target_name=target_spec)
    paths = write_reports(report_dir, report, thresholds)
    passed = all_passed(report, thresholds)

    summary_path: str | None = None
    if ci_summary:
        summary_path = github_actions_summary(markdown_report(report, thresholds, passed=passed))

    return LabEvalResult(
        target_name=report.target_name,
        metrics=report.metrics,
        report_paths=paths,
        passed=passed,
        summary_path=summary_path,
    )


def thresholds_from_json(path: str | Path | None) -> dict[str, float] | None:
    """Load a thresholds JSON file; returns None when not provided."""
    if not path:
        return None
    import json

    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"thresholds file must be a JSON object: {path}")
    parsed: dict[str, float] = {}
    for key, value in data.items():
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            parsed[key] = float(value)
    return parsed or None


def default_thresholds() -> dict[str, float]:
    """Return a copy of the lab's default pass thresholds."""
    return dict(DEFAULT_THRESHOLDS)
