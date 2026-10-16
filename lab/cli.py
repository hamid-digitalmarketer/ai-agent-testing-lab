"""Command-line entry point: ``lab-eval`` / ``python -m lab.cli``.

Runs the full evaluation for a target repository and emits CI artifacts.
Example:

    lab-eval --target demo.runner:build_agents \\
             --datasets evaluation/datasets \\
             --report-dir evaluation/results \\
             --ci-summary
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from lab.integration import run_lab_eval, thresholds_from_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lab-eval",
        description="Evaluate a target repo's agents with ai-agent-testing-lab.",
    )
    parser.add_argument(
        "--target",
        required=True,
        help="Import spec of the agents factory, e.g. 'demo.runner:build_agents'",
    )
    parser.add_argument(
        "--datasets",
        default="evaluation/datasets",
        help="Directory containing the seven labeled datasets",
    )
    parser.add_argument(
        "--report-dir",
        default="evaluation/results",
        help="Where metrics.json / report.md / dashboard.html are written",
    )
    parser.add_argument(
        "--thresholds",
        default=None,
        help="Optional JSON file overriding pass thresholds",
    )
    parser.add_argument(
        "--reliability-runs",
        type=int,
        default=6,
        help="Number of repeated runs for the reliability suite",
    )
    parser.add_argument(
        "--ci-summary",
        action="store_true",
        help="Append the Markdown report to $GITHUB_STEP_SUMMARY",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run_lab_eval(
            target_spec=args.target,
            datasets_dir=args.datasets,
            report_dir=args.report_dir,
            thresholds=thresholds_from_json(args.thresholds),
            ci_summary=args.ci_summary,
            reliability_runs=args.reliability_runs,
        )
    except Exception as exc:  # noqa: BLE001 - CLI must surface a clean message
        print(f"lab-eval failed: {exc}", file=sys.stderr)
        return 2

    print(f"target        : {result.target_name}")
    print(f"overall       : {'PASS' if result.passed else 'FAIL'}")
    for metric in sorted(result.metrics):
        print(f"  {metric:<32} {result.metrics[metric]:.3f}")
    for kind, path in result.report_paths.items():
        print(f"report ({kind}): {path}")
    if result.summary_path:
        print(f"ci summary    : {result.summary_path}")
    return 0 if result.passed else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
