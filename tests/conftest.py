"""Shared fixtures for the lab test suite."""

from __future__ import annotations

from ai_marketing_shared.schemas import (
    AgentRun,
    Confidence,
    Effort,
    Evidence,
    Priority,
    Recommendation,
    ToolCall,
)


def make_run(
    *,
    agent: str = "tester",
    tools: list[str] | None = None,
    success: bool = True,
    latency_ms: int = 10,
    token_cost: float = 0.0,
    api_cost: float = 0.0,
) -> AgentRun:
    """Build a minimal AgentRun for metric unit tests."""
    run = AgentRun(
        agent=agent,
        input_summary="unit test",
        tool_calls=[
            ToolCall(
                tool_name=name,
                arguments={},
                result_summary="ok",
                latency_ms=1,
                success=True,
            )
            for name in (tools or [])
        ],
        recommendations=[],
        token_cost=token_cost,
        api_cost_estimate=api_cost,
    )
    run.finish(status="completed" if success else "failed")
    run.latency_ms = latency_ms
    return run


def make_recommendation(
    *,
    agent: str = "tester",
    issue: str = "Sample issue",
    evidence_metric: str = "organic_clicks",
    evidence_value: float = 1200.0,
    proposed_action: str = "Refresh landing pages",
    requires_approval: bool = True,
    expected_impact: str = "+5% clicks",
    effort: Effort = Effort.MEDIUM,
    priority: Priority = Priority.MEDIUM,
    confidence: Confidence = Confidence.MEDIUM,
) -> Recommendation:
    """Build a complete Recommendation for quality tests."""
    return Recommendation(
        agent=agent,
        issue=issue,
        evidence=[
            Evidence(
                source="sample_data",
                metric=evidence_metric,
                value=evidence_value,
                confidence_interval=(evidence_value * 0.9, evidence_value * 1.1),
            )
        ],
        priority=priority,
        confidence=confidence,
        expected_impact=expected_impact,
        effort=effort,
        proposed_action=proposed_action,
        next_steps=["Measure after 14 days"],
        requires_approval=requires_approval,
    )
