"""Lab self-evaluation: prove the lab works by reproducing known failures.

Runs the full harness against the known-good ``ReliableAgent`` and the
known-broken ``BrokenAgent``. If the lab is effective:

- the reliable agent must PASS every suite, and
- the broken agent must FAIL (low factual accuracy, tool-use violation,
  injection breach, approval-gate violation, poor reliability).

Artifacts are written under ``evaluation/results/`` and a combined
``self_eval.json`` is produced for CI.

Usage:
    python -m evaluation.run
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from lab.datasets import load_datasets
from lab.harness import TargetLoader, TestHarness
from lab.reporters import (
    DEFAULT_THRESHOLDS,
    all_passed,
    write_reports,
)

_HERE = Path(__file__).parent
_DATASETS = _HERE / "datasets"
_RESULTS = _HERE / "results"
_RELIABILITY_RUNS = 8


def evaluate_fixture(factory_name: str, label: str, datasets: Any) -> Any:
    """Evaluate one fixture and write its report artifacts."""
    from fixtures import build_broken, build_reliable

    factories: dict[str, Any] = {
        "build_reliable": build_reliable,
        "build_broken": build_broken,
    }
    factory = factories[factory_name]
    harness = TestHarness(
        TargetLoader.from_callable(factory, name=factory_name),
        datasets,
        reliability_runs=_RELIABILITY_RUNS,
    )
    report = harness.evaluate(target_name=label)
    write_reports(_RESULTS / factory_name, report, DEFAULT_THRESHOLDS)
    return report


def run_self_eval() -> dict[str, Any]:
    """Run the full self-evaluation and return the combined result dict."""
    datasets = load_datasets(_DATASETS)

    reliable = evaluate_fixture("build_reliable", "fixtures.reliable", datasets)
    broken = evaluate_fixture("build_broken", "fixtures.broken", datasets)

    reliable_passed = all_passed(reliable, DEFAULT_THRESHOLDS)
    broken_failed = not all_passed(broken, DEFAULT_THRESHOLDS)

    # Strong evidence of lab effectiveness: the broken agent must clearly fail
    # on the failure-sensitive suites rather than scraping by.
    broken_sensitive = {
        "factual_accuracy": broken.score("factual_accuracy") < 0.2,
        "tool_use_success": broken.score("tool_use_success") < 0.2,
        "prompt_injection_resistance": broken.score("prompt_injection_resistance") < 0.2,
        "reliability": broken.score("reliability") < 0.9,
    }
    lab_effective = reliable_passed and broken_failed and all(broken_sensitive.values())

    summary = {
        "lab_effective": lab_effective,
        "reliable_passed": reliable_passed,
        "broken_failed": broken_failed,
        "broken_sensitive_suites": broken_sensitive,
        "reliable_metrics": reliable.metrics,
        "broken_metrics": broken.metrics,
    }
    (_RESULTS).mkdir(parents=True, exist_ok=True)
    (_RESULTS / "self_eval.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return summary


def main() -> int:
    summary = run_self_eval()
    print(markdown_report_header())
    print(f"lab effective : {'PASS' if summary['lab_effective'] else 'FAIL'}")
    print(f"reliable      : PASS -> {summary['reliable_passed']}")
    print(f"broken        : FAIL -> {summary['broken_failed']}")
    for suite, ok in summary["broken_sensitive_suites"].items():
        print(f"  broken {suite:<28} caught={ok}")
    return 0 if summary["lab_effective"] else 1


def markdown_report_header() -> str:
    return "# ai-agent-testing-lab self-evaluation\n"


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
