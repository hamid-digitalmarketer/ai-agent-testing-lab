"""Test harness: loads agents from any repo and evaluates them against the lab.

The harness is deliberately decoupled from any single repository. A "target"
is anything that yields ``{name: agent}`` where ``agent.run(input_summary=...)
`` returns an ``AgentRun`` (or a JSON-dict convertible to one). Two standard
ways to load a target:

- ``TargetLoader.from_import("demo.runner:build_agents")`` - import a factory
  from an installed package (used for ``ai-marketing-growth-os`` and every
  downstream repo).
- ``TargetLoader.from_callable(fn)`` - pass a callable directly (used by the
  lab's own fixtures and by inline pytest evaluation).

Evaluation replays the seven labeled datasets, produces one ``LabReport`` with
metrics and per-suite detail text, and never touches a live API: agents are
expected to run in their rule-based demo mode.
"""

from __future__ import annotations

import importlib
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from ai_marketing_shared.schemas import AgentRun

from lab.datasets import LabDatasets, load_datasets
from lab.metrics import (
    calibration_error,
    classification_metrics,
    confidence_score,
    cost_control,
    latency_budget,
    recommendation_quality,
    reliability,
    tool_use_success,
)

AgentFactory = Callable[[], dict[str, Any]]


class AgentLoadError(Exception):
    """Raised when a target cannot be imported or does not yield agents."""


@dataclass
class LabReport:
    """Complete evaluation result for one target under test."""

    target_name: str
    metrics: dict[str, float] = field(default_factory=dict)
    details: dict[str, str] = field(default_factory=dict)
    dataset_summary: dict[str, int] = field(default_factory=dict)
    agent_names: list[str] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def score(self, metric: str) -> float:
        return self.metrics.get(metric, 0.0)


class TargetLoader:
    """Factory for agent-loading callables."""

    @staticmethod
    def from_import(spec: str) -> AgentFactory:
        """Create a factory from ``"module.path:attr"`` (or ``"module.path"``).

        The attribute, when called, must return a mapping of agent name to
        agent object with a ``run(input_summary=...)`` method.
        """
        module_path, _, attr = spec.partition(":")
        attr = attr or "build_agents"

        def factory() -> dict[str, Any]:
            try:
                module = importlib.import_module(module_path)
            except ImportError as exc:
                raise AgentLoadError(f"could not import target module '{module_path}': {exc}") from exc
            if not hasattr(module, attr):
                raise AgentLoadError(f"target module '{module_path}' has no attribute '{attr}'")
            agents = getattr(module, attr)()
            return TargetLoader._validate_agents(agents, f"{module_path}:{attr}")

        return factory

    @staticmethod
    def from_callable(fn: Callable[[], dict[str, Any]], *, name: str = "callable") -> AgentFactory:
        """Create a factory from an existing zero-argument callable."""

        def factory() -> dict[str, Any]:
            agents = fn()
            return TargetLoader._validate_agents(agents, name)

        return factory

    @staticmethod
    def _validate_agents(agents: Any, source: str) -> dict[str, Any]:
        if agents is None:
            raise AgentLoadError(f"target '{source}' returned None")
        if not isinstance(agents, dict):
            raise AgentLoadError(
                f"target '{source}' must return a dict[str, agent], got {type(agents).__name__}"
            )
        if not agents:
            raise AgentLoadError(f"target '{source}' returned no agents")
        bad = [name for name in agents.values() if not hasattr(name, "run")]
        if bad:
            raise AgentLoadError(f"target '{source}' contains {len(bad)} object(s) without a run() method")
        return agents


class TestHarness:
    """Runs the full seven-suite evaluation against a loaded target."""

    def __init__(
        self,
        agents_factory: AgentFactory,
        datasets: LabDatasets,
        *,
        reliability_runs: int = 6,
        default_input: str = "evaluate agent on sample marketing data",
    ) -> None:
        self.agents_factory = agents_factory
        self.datasets = datasets
        self.reliability_runs = reliability_runs
        self.default_input = default_input

    # -- public API ---------------------------------------------------------

    def evaluate(self, *, target_name: str | None = None) -> LabReport:
        agents = self.agents_factory()
        names = sorted(agents)
        label = target_name or f"{len(names)} agents"

        runs = self._run_all_agents(agents, self.default_input)
        factual_score, cm = self._score_factual(agents, runs)
        injection_score, injection_cm = self._score_injection(agents)
        combined_cm = self._combine_confusion(cm, injection_cm)
        cls = classification_metrics(**combined_cm)
        confidences, hits = self._calibration_pairs(agents, runs)
        cost_total = sum(run.api_cost_estimate + run.token_cost for run in runs)
        latency_total = sum(run.latency_ms for run in runs)
        reliability_score = self._score_reliability(agents)

        metrics = {
            "accuracy": cls["accuracy"],
            "precision": cls["precision"],
            "recall": cls["recall"],
            "f1": cls["f1"],
            "calibration": calibration_error(confidences, hits),
            "factual_accuracy": factual_score,
            "tool_use_success": tool_use_success(runs, self.datasets.tool_use),
            "recommendation_quality": recommendation_quality(runs, self.datasets.recommendation_quality),
            "prompt_injection_resistance": injection_score,
            "cost_control": cost_control(cost_total, self.datasets.cost),
            "latency_budget": latency_budget(latency_total, self.datasets.latency),
            "reliability": reliability_score,
        }
        details = {
            "factual_accuracy": self._detail_factual(cm),
            "prompt_injection_resistance": self._detail_injection(injection_cm),
            "cost_control": (
                f"measured ${cost_total:.4f} "
                f"(cap ${float(self.datasets.cost.data.get('max_cost_usd', 0.0)):.2f})"
            ),
            "latency_budget": (
                f"measured {latency_total}ms "
                f"(budget {int(self.datasets.latency.data.get('max_latency_ms', 0))}ms)"
            ),
            "reliability": (f"{reliability_score:.1%} completion over {self.reliability_runs} attempt(s)"),
        }
        summary = {
            "factual_accuracy": len(self.datasets.factual_accuracy.cases()),
            "tool_use": len(self.datasets.tool_use.cases()),
            "recommendation_quality": 1,
            "prompt_injection": len(self.datasets.prompt_injection.cases()) * max(1, len(names)),
            "cost": 1,
            "latency": 1,
            "reliability": self.reliability_runs,
        }
        return LabReport(
            target_name=label,
            metrics=metrics,
            details=details,
            dataset_summary=summary,
            agent_names=names,
        )

    # -- helpers ------------------------------------------------------------

    def run_agent(self, agent: Any, input_summary: str) -> AgentRun:
        """Run one agent safely, converting failures into a FAILED AgentRun."""
        try:
            result = agent.run(input_summary=input_summary)
        except Exception as exc:  # noqa: BLE001 - lab must never crash on agent bugs
            run = AgentRun(agent=getattr(agent, "name", "unknown"), input_summary=input_summary)
            run.finish(status="failed", error=f"{type(exc).__name__}: {exc}")
            return run
        if isinstance(result, AgentRun):
            return result
        if isinstance(result, dict):
            try:
                return AgentRun.model_validate(result)
            except Exception as exc:  # noqa: BLE001
                run = AgentRun(agent=getattr(agent, "name", "unknown"), input_summary=input_summary)
                run.finish(status="failed", error=f"invalid AgentRun payload: {exc}")
                return run
        run = AgentRun(agent=getattr(agent, "name", "unknown"), input_summary=input_summary)
        run.finish(status="failed", error="agent run() did not return AgentRun or dict")
        return run

    def _run_all_agents(self, agents: dict[str, Any], input_summary: str) -> list[AgentRun]:
        runs: list[AgentRun] = []
        for agent in agents.values():
            started = time.monotonic()
            run = self.run_agent(agent, input_summary)
            run.latency_ms = max(run.latency_ms, int((time.monotonic() - started) * 1000))
            runs.append(run)
        return runs

    def _score_factual(self, agents: dict[str, Any], runs: list[AgentRun]) -> tuple[float, dict[str, int]]:
        cases = self.datasets.factual_accuracy.cases()
        hits = 0
        misses = 0
        recs_by_agent: dict[str, list[Any]] = {}
        for run in runs:
            recs_by_agent.setdefault(run.agent, []).extend(run.recommendations)
        for case in cases:
            agent = case.get("agent", "")
            expected_issue = case.get("issue_contains", "")
            expected_metric = case.get("evidence_metric", "")
            lo, hi = case.get("expected_value_range", [float("-inf"), float("inf")])
            matched = False
            for rec in recs_by_agent.get(agent, []):
                if expected_issue and expected_issue not in rec.issue:
                    continue
                for evidence in rec.evidence:
                    if expected_metric and evidence.metric != expected_metric:
                        continue
                    if lo <= evidence.value <= hi:
                        matched = True
                        break
                if matched:
                    break
            if matched:
                hits += 1
            else:
                misses += 1
        total = hits + misses
        score = hits / total if total else 0.0
        return score, {"tp": hits, "fn": misses, "fp": 0, "tn": 0}

    def _score_injection(self, agents: dict[str, Any]) -> tuple[float, dict[str, int]]:
        dataset = self.datasets.prompt_injection
        cases = dataset.cases()
        forbidden: list[str] = dataset.data.get("forbidden_tools", [])
        safe = 0
        unsafe = 0
        for case in cases:
            for agent in agents.values():
                run = self.run_agent(agent, case.get("input_summary", ""))
                # A failed run cannot prove injection resistance; count it as unsafe.
                if run.status == "failed":
                    unsafe += 1
                elif all(call.tool_name not in forbidden for call in run.tool_calls):
                    safe += 1
                else:
                    unsafe += 1
        total = safe + unsafe
        score = safe / total if total else 0.0
        return score, {"tp": 0, "fn": 0, "fp": unsafe, "tn": safe}

    @staticmethod
    def _combine_confusion(factual_cm: dict[str, int], injection_cm: dict[str, int]) -> dict[str, int]:
        return {
            "tp": factual_cm["tp"] + injection_cm["tp"],
            "fp": factual_cm["fp"] + injection_cm["fp"],
            "fn": factual_cm["fn"] + injection_cm["fn"],
            "tn": factual_cm["tn"] + injection_cm["tn"],
        }

    def _calibration_pairs(
        self, agents: dict[str, Any], runs: list[AgentRun]
    ) -> tuple[list[float], list[bool]]:
        cases = self.datasets.factual_accuracy.cases()
        recs_by_agent: dict[str, list[Any]] = {}
        for run in runs:
            recs_by_agent.setdefault(run.agent, []).extend(run.recommendations)
        confidences: list[float] = []
        hits: list[bool] = []
        for case in cases:
            agent = case.get("agent", "")
            expected_issue = case.get("issue_contains", "")
            expected_metric = case.get("evidence_metric", "")
            lo, hi = case.get("expected_value_range", [float("-inf"), float("inf")])
            matched = False
            conf = 0.6
            for rec in recs_by_agent.get(agent, []):
                conf = confidence_score(rec)
                if expected_issue and expected_issue not in rec.issue:
                    continue
                for evidence in rec.evidence:
                    if expected_metric and evidence.metric != expected_metric:
                        continue
                    if lo <= evidence.value <= hi:
                        matched = True
                        break
                if matched:
                    break
            confidences.append(conf)
            hits.append(matched)
        return confidences, hits

    def _score_reliability(self, agents: dict[str, Any]) -> float:
        attempts: list[list[AgentRun]] = []
        for _ in range(self.reliability_runs):
            attempts.append(self._run_all_agents(agents, self.default_input))
        return reliability(attempts, self.datasets.reliability)

    @staticmethod
    def _detail_factual(cm: dict[str, int]) -> str:
        total = cm["tp"] + cm["fn"]
        return f"{cm['tp']}/{total} labeled factual cases matched with expected evidence"

    @staticmethod
    def _detail_injection(cm: dict[str, int]) -> str:
        total = cm["tn"] + cm["fp"]
        return f"{cm['tn']}/{total} adversarial runs remained safe (no forbidden write tool)"


def evaluate_target(
    *,
    agents_factory: AgentFactory,
    datasets: LabDatasets,
    target_name: str | None = None,
    reliability_runs: int = 6,
) -> LabReport:
    """Convenience wrapper around ``TestHarness.evaluate``."""
    harness = TestHarness(agents_factory, datasets, reliability_runs=reliability_runs)
    return harness.evaluate(target_name=target_name)


DEFAULT_DATASETS_DIR = "evaluation/datasets"


def load_default_datasets(datasets_dir: str | None = None) -> LabDatasets:
    """Load datasets from the repo-default location (or an explicit path)."""
    return load_datasets(datasets_dir or DEFAULT_DATASETS_DIR)
