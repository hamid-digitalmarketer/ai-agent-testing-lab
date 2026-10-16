#!/usr/bin/env python3
"""Quick local demo of the lab.

Runs the lab self-evaluation against its built-in fixtures (known-good and
known-broken agents) and prints the Markdown report. Use this to verify the
lab works before wiring it into CI.

Usage:
    python scripts/demo_eval.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from evaluation.run import run_self_eval  # noqa: E402


def main() -> int:
    print("Running ai-agent-testing-lab demo evaluation...\n")
    summary = run_self_eval()
    print("=" * 72)
    print(f"lab effective : {summary['lab_effective']}")
    print(f"reliable pass : {summary['reliable_passed']}")
    print(f"broken fail   : {summary['broken_failed']}")
    print("=" * 72)

    md_path = _ROOT / "evaluation" / "results" / "build_reliable" / "report.md"
    dashboard = _ROOT / "evaluation" / "results" / "build_reliable" / "dashboard.html"
    if md_path.exists():
        print(md_path.read_text(encoding="utf-8"))
    print(f"Artifacts under: {_ROOT / 'evaluation' / 'results'}")
    print(f"Open the dashboard in a browser: {dashboard}")
    return 0 if summary["lab_effective"] else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
