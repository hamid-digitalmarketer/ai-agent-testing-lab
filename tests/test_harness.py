"""Unit tests for lab.harness (TargetLoader, TestHarness, LabReport)."""

from __future__ import annotations

import pytest
from ai_marketing_shared.schemas import AgentRun
from fixtures import BrokenAgent, ReliableAgent
from lab.datasets import load_datasets
from lab.harness import (
    AgentLoadError,
    LabReport,
    TargetLoader,
    TestHarness,
    load_default_datasets,
)

_DATASETS = "evaluation/datasets"


def _datasets():
    return load_datasets(_DATASETS)


# -- TargetLoader -----------------------------------------------------------


def test_from_import_valid_factory():
    factory = TargetLoader.from_import("fixtures:build_reliable")
    agents = factory()
    assert "reliable" in agents


def test_from_import_default_attr():
    factory = TargetLoader.from_import("fixtures")
    agents = factory()
    assert "reliable" in agents or "broken" in agents


def test_from_import_module_missing():
    factory = TargetLoader.from_import("no_such_module:build_agents")
    with pytest.raises(AgentLoadError, match="could not import"):
        factory()


def test_from_import_attr_missing():
    factory = TargetLoader.from_import("fixtures:no_such_attr")
    with pytest.raises(AgentLoadError, match="no attribute"):
        factory()


def test_from_import_returns_none():
    factory = TargetLoader.from_import("fixtures:build_none_factory")
    with pytest.raises(AgentLoadError, match="returned None"):
        factory()


def test_from_import_non_dict():
    factory = TargetLoader.from_import("fixtures:build_list_factory")
    with pytest.raises(AgentLoadError, match="must return a dict"):
        factory()


def test_from_import_empty_dict():
    factory = TargetLoader.from_import("fixtures:build_empty_factory")
    with pytest.raises(AgentLoadError, match="no agents"):
        factory()


def test_from_import_agent_without_run():
    factory = TargetLoader.from_import("fixtures:build_bad_agent_factory")
    with pytest.raises(AgentLoadError, match="without a run"):
        factory()


def test_from_callable_validates():
    def good():
        return {"a": ReliableAgent()}

    factory = TargetLoader.from_callable(good, name="good")
    assert "a" in factory()

    def bad():
        return {"a": object()}

    with pytest.raises(AgentLoadError, match="without a run"):
        TargetLoader.from_callable(bad, name="bad")()


# -- TestHarness ------------------------------------------------------------


def test_evaluate_reliable_passes_all_suites():
    harness = TestHarness(
        TargetLoader.from_callable(lambda: {"reliable": ReliableAgent()}),
        _datasets(),
        reliability_runs=4,
    )
    report = harness.evaluate(target_name="reliable-fixture")
    assert report.target_name == "reliable-fixture"
    assert report.agent_names == ["reliable"]
    assert report.score("factual_accuracy") == 1.0
    assert report.score("tool_use_success") == 1.0
    assert report.score("recommendation_quality") == 1.0
    assert report.score("prompt_injection_resistance") == 1.0
    assert report.score("cost_control") == 1.0
    assert report.score("latency_budget") == 1.0
    assert report.score("reliability") == 1.0


def test_evaluate_broken_fails_sensitive_suites():
    harness = TestHarness(
        TargetLoader.from_callable(lambda: {"broken": BrokenAgent(fail_rate=1.0)}),
        _datasets(),
        reliability_runs=4,
    )
    report = harness.evaluate(target_name="broken-fixture")
    assert report.score("factual_accuracy") == 0.0
    assert report.score("tool_use_success") == 0.0
    assert report.score("recommendation_quality") == 0.0
    assert report.score("prompt_injection_resistance") == 0.0
    assert report.score("reliability") == 0.0


def test_run_agent_handles_exceptions():
    class Exploding:
        name = "boom"

        def run(self, input_summary=""):
            raise ValueError("kaboom")

    harness = TestHarness(TargetLoader.from_callable(lambda: {"boom": Exploding()}), _datasets())
    run = harness.run_agent(Exploding(), "x")
    assert run.status == "failed"
    assert "kaboom" in run.error


def test_run_agent_accepts_dict_payload():
    class DictAgent:
        name = "dict"

        def run(self, input_summary=""):
            return {
                "agent": "dict",
                "input_summary": input_summary,
                "tool_calls": [],
                "recommendations": [],
                "token_cost": 0.0,
                "api_cost_estimate": 0.0,
            }

    harness = TestHarness(TargetLoader.from_callable(lambda: {"dict": DictAgent()}), _datasets())
    run = harness.run_agent(DictAgent(), "y")
    assert isinstance(run, AgentRun)
    assert run.agent == "dict"


def test_run_agent_rejects_invalid_payload():
    class BadDictAgent:
        name = "bad"

        def run(self, input_summary=""):
            return {"not": "an agent run"}

    harness = TestHarness(TargetLoader.from_callable(lambda: {"bad": BadDictAgent()}), _datasets())
    run = harness.run_agent(BadDictAgent(), "y")
    assert run.status == "failed"
    assert "invalid AgentRun payload" in run.error


def test_run_agent_rejects_wrong_return_type():
    class WrongAgent:
        name = "wrong"

        def run(self, input_summary=""):
            return 42

    harness = TestHarness(TargetLoader.from_callable(lambda: {"wrong": WrongAgent()}), _datasets())
    run = harness.run_agent(WrongAgent(), "y")
    assert run.status == "failed"
    assert "did not return AgentRun or dict" in run.error


def test_lab_report_score_default():
    report = LabReport(target_name="t", metrics={"accuracy": 0.9})
    assert report.score("accuracy") == 0.9
    assert report.score("missing") == 0.0


def test_evaluate_target_and_default_datasets(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # default path points at evaluation/datasets relative to cwd; build a fake one
    (tmp_path / "evaluation" / "datasets").mkdir(parents=True)
    import json

    from lab.datasets import dataset_names

    for name in dataset_names():
        (tmp_path / "evaluation" / "datasets" / f"{name}.json").write_text(
            json.dumps({"name": name}), encoding="utf-8"
        )
    datasets = load_default_datasets()
    assert set(datasets.as_dict().keys()) == set(dataset_names())
