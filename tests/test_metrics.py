"""Unit tests for lab.metrics."""

from __future__ import annotations

import pytest
from ai_marketing_shared.schemas import Confidence
from lab.datasets import LabDataset
from lab.metrics import (
    calibration_error,
    classification_metrics,
    confidence_score,
    cost_control,
    factual_accuracy,
    latency_budget,
    prompt_injection_resistance,
    recommendation_quality,
    reliability,
    tool_use_success,
)

from tests.conftest import make_recommendation, make_run

# -- classification ---------------------------------------------------------


def test_classification_metrics_perfect():
    out = classification_metrics(tp=10, fp=0, fn=0, tn=5)
    assert out == {"accuracy": 1.0, "precision": 1.0, "recall": 1.0, "f1": 1.0}


def test_classification_metrics_no_positives():
    out = classification_metrics(tp=0, fp=0, fn=0, tn=3)
    assert out["accuracy"] == 1.0
    assert out["precision"] == 0.0
    assert out["recall"] == 0.0
    assert out["f1"] == 0.0


def test_classification_metrics_typical():
    out = classification_metrics(tp=8, fp=2, fn=4, tn=10)
    assert out["accuracy"] == 18 / 24
    assert out["precision"] == 0.8
    assert out["recall"] == 8 / 12


# -- factual accuracy -------------------------------------------------------


def test_factual_accuracy_hits_and_misses():
    dataset = LabDataset(
        name="factual_accuracy",
        data={
            "cases": [
                {
                    "agent": "a",
                    "issue_contains": "organic",
                    "evidence_metric": "clicks",
                    "expected_value_range": [1000, 1500],
                },
                {
                    "agent": "a",
                    "issue_contains": "paid",
                    "evidence_metric": "spend",
                    "expected_value_range": [100, 200],
                },
            ]
        },
    )
    run = make_run(agent="a")
    run.recommendations = [
        make_recommendation(
            agent="a",
            issue="organic declined",
            evidence_metric="clicks",
            evidence_value=1200.0,
        )
    ]
    assert factual_accuracy([run], dataset) == 0.5


def test_factual_accuracy_empty_cases():
    dataset = LabDataset(name="factual_accuracy", data={"cases": []})
    assert factual_accuracy([make_run()], dataset) == 0.0


# -- tool use ---------------------------------------------------------------


def test_tool_use_success_requires_and_forbids():
    dataset = LabDataset(
        name="tool_use",
        data={
            "required_tool_calls": {"a": ["fetch_metrics", "analyze"]},
            "forbidden_tools": ["execute_campaign_change"],
        },
    )
    good = make_run(agent="a", tools=["fetch_metrics", "analyze"])
    assert tool_use_success([good], dataset) == 1.0
    missing = make_run(agent="a", tools=["fetch_metrics"])
    assert tool_use_success([missing], dataset) == 0.5


def test_tool_use_forbidden_call_zeroes_score():
    dataset = LabDataset(
        name="tool_use",
        data={"required_tool_calls": {}, "forbidden_tools": ["execute_campaign_change"]},
    )
    bad = make_run(agent="a", tools=["fetch_metrics", "execute_campaign_change"])
    assert tool_use_success([bad], dataset) == 0.0


def test_tool_use_no_requirements_returns_one():
    dataset = LabDataset(name="tool_use", data={"required_tool_calls": {}, "forbidden_tools": []})
    assert tool_use_success([make_run(agent="a")], dataset) == 1.0


# -- recommendation quality -------------------------------------------------


def test_recommendation_quality_complete_passes():
    dataset = LabDataset(
        name="recommendation_quality",
        data={
            "required_fields": [
                "issue",
                "priority",
                "confidence",
                "expected_impact",
                "effort",
                "proposed_action",
                "requires_approval",
            ],
            "min_evidence_per_rec": 1,
            "agents_present": ["tester"],
        },
    )
    run = make_run(agent="tester")
    run.recommendations = [make_recommendation(agent="tester")]
    assert recommendation_quality([run], dataset) == 1.0


def test_recommendation_quality_missing_fields_fails():
    dataset = LabDataset(
        name="recommendation_quality",
        data={"required_fields": ["expected_impact"], "min_evidence_per_rec": 1},
    )
    from ai_marketing_shared.schemas import Recommendation

    rec = Recommendation(agent="tester", issue="x", proposed_action="y")
    run = make_run(agent="tester")
    run.recommendations = [rec]
    assert recommendation_quality([run], dataset) == 0.0


def test_recommendation_quality_write_without_approval_fails():
    dataset = LabDataset(
        name="recommendation_quality",
        data={
            "required_fields": ["proposed_action", "requires_approval"],
            "min_evidence_per_rec": 1,
        },
    )
    run = make_run(agent="tester")
    run.recommendations = [
        make_recommendation(
            agent="tester",
            proposed_action="execute_campaign_change to double budget",
            requires_approval=False,
        )
    ]
    assert recommendation_quality([run], dataset) == 0.0


def test_recommendation_quality_no_recs_zero():
    dataset = LabDataset(name="recommendation_quality", data={"required_fields": []})
    assert recommendation_quality([make_run(agent="tester")], dataset) == 0.0


def test_recommendation_quality_missing_agent_penalty():
    dataset = LabDataset(
        name="recommendation_quality",
        data={"required_fields": [], "min_evidence_per_rec": 0, "agents_present": ["ghost"]},
    )
    run = make_run(agent="tester")
    run.recommendations = [make_recommendation(agent="tester")]
    score = recommendation_quality([run], dataset)
    assert score == min(1.0, 0.9)


# -- prompt injection -------------------------------------------------------


def test_prompt_injection_resistance_safe():
    dataset = LabDataset(
        name="prompt_injection",
        data={"forbidden_tools": ["execute_campaign_change"], "cases": [{"id": 1}, {"id": 2}]},
    )
    agents = {"safe": type("A", (), {"name": "safe"})(), "safe2": type("B", (), {"name": "safe2"})()}

    def run_fn(agent, prompt):
        return make_run(agent=agent.name, tools=["fetch_metrics"])

    assert prompt_injection_resistance(agents, dataset, run_fn=run_fn) == 1.0


def test_prompt_injection_resistance_unsafe():
    dataset = LabDataset(
        name="prompt_injection",
        data={"forbidden_tools": ["execute_campaign_change"], "cases": [{"id": 1}]},
    )
    agents = {"bad": type("A", (), {"name": "bad"})()}

    def run_fn(agent, prompt):
        return make_run(agent=agent.name, tools=["execute_campaign_change"])

    assert prompt_injection_resistance(agents, dataset, run_fn=run_fn) == 0.0


# -- cost / latency / reliability ------------------------------------------


def test_cost_control_within_and_over():
    dataset = LabDataset(name="cost", data={"max_cost_usd": 0.0})
    assert cost_control(0.0, dataset) == 1.0
    assert cost_control(0.01, dataset) == 0.0


def test_latency_budget_within_and_over():
    dataset = LabDataset(name="latency", data={"max_latency_ms": 5000})
    assert latency_budget(5000, dataset) == 1.0
    assert latency_budget(5001, dataset) == 0.0


def test_reliability_completion_rate():
    dataset = LabDataset(name="reliability", data={})
    attempts = [
        [make_run(agent="a", success=True), make_run(agent="b", success=False)],
        [make_run(agent="a", success=True), make_run(agent="b", success=False)],
    ]
    assert reliability(attempts, dataset) == 0.5


def test_reliability_empty():
    dataset = LabDataset(name="reliability", data={})
    assert reliability([], dataset) == 0.0


# -- calibration ------------------------------------------------------------


def test_calibration_error_perfect():
    # Mean confidence 0.8, hit rate 1.0 -> 1 - |0.8 - 1.0| = 0.8.
    assert calibration_error([0.8, 0.8, 0.8], [True, True, True]) == pytest.approx(0.8)


def test_calibration_error_mismatch():
    # Mean confidence 0.9, hit rate 0.0 -> 1 - |0.9 - 0.0| = 0.1.
    assert calibration_error([0.9, 0.9], [False, False]) == pytest.approx(0.1)


def test_calibration_error_bad_inputs():
    assert calibration_error([], []) == 0.0
    assert calibration_error([0.5, 0.5], [True]) == 0.0


def test_confidence_score_maps_enum():
    assert confidence_score(make_recommendation(confidence=Confidence.LOW)) == 0.3
    assert confidence_score(make_recommendation(confidence=Confidence.MEDIUM)) == 0.6
    assert confidence_score(make_recommendation(confidence=Confidence.HIGH)) == 0.9
