"""Self-evaluation tests: the lab must catch the broken agent.

These tests exercise the same self-evaluation that ``evaluation/run.py`` runs
in CI, but with fewer reliability repeats to keep the suite fast.
"""

from __future__ import annotations

import json

import evaluation.run as evaluation_run
from evaluation.run import evaluate_fixture, main, run_self_eval
from fixtures import build_broken
from lab.datasets import load_datasets
from lab.harness import TargetLoader, TestHarness
from lab.reporters import DEFAULT_THRESHOLDS, all_passed

_DATASETS = "evaluation/datasets"


def _datasets():
    return load_datasets(_DATASETS)


def test_reliable_agent_passes_self_eval(tmp_path):
    report = evaluate_fixture("build_reliable", "fixtures.reliable", _datasets())
    assert all_passed(report, DEFAULT_THRESHOLDS)


def test_broken_agent_fails_self_eval():
    report = evaluate_fixture("build_broken", "fixtures.broken", _datasets())
    assert not all_passed(report, DEFAULT_THRESHOLDS)
    assert report.score("factual_accuracy") < 0.2
    assert report.score("tool_use_success") < 0.2
    assert report.score("prompt_injection_resistance") < 0.2
    assert report.score("reliability") < 0.9


def test_run_self_eval_reports_effective_lab():
    summary = run_self_eval()
    assert summary["lab_effective"] is True
    assert summary["reliable_passed"] is True
    assert summary["broken_failed"] is True
    assert all(summary["broken_sensitive_suites"].values())
    assert (json.loads(_load_self_eval())["lab_effective"]) is True


def _load_self_eval():
    from pathlib import Path

    return (Path("evaluation/results/self_eval.json")).read_text(encoding="utf-8")


def test_harness_reproduces_known_failure_with_small_runs():
    harness = TestHarness(
        TargetLoader.from_callable(build_broken, name="broken"),
        _datasets(),
        reliability_runs=3,
    )
    report = harness.evaluate(target_name="broken-smoke")
    assert report.score("reliability") < 0.9


def _fake_summary(lab_effective):
    return {
        "lab_effective": lab_effective,
        "reliable_passed": lab_effective,
        "broken_failed": lab_effective,
        "broken_sensitive_suites": {
            "factual_accuracy": lab_effective,
            "tool_use_success": lab_effective,
            "prompt_injection_resistance": lab_effective,
            "reliability": lab_effective,
        },
    }


def test_main_returns_zero_when_effective(monkeypatch, capsys):
    monkeypatch.setattr(evaluation_run, "run_self_eval", lambda: _fake_summary(True))
    assert main() == 0
    out = capsys.readouterr().out
    assert "PASS" in out
    assert "reliable" in out


def test_main_returns_one_when_ineffective(monkeypatch, capsys):
    monkeypatch.setattr(evaluation_run, "run_self_eval", lambda: _fake_summary(False))
    assert main() == 1
    out = capsys.readouterr().out
    assert "FAIL" in out
