"""Unit tests for the lab's known-good / known-broken fixtures."""

from __future__ import annotations

import pytest
from fixtures import BrokenAgent, ReliableAgent


def test_reliable_agent_produces_complete_safe_run():
    run = ReliableAgent().run("demo")
    assert run.status == "completed"
    assert len(run.recommendations) == 2
    for rec in run.recommendations:
        assert rec.evidence
        assert rec.requires_approval is True
        assert rec.expected_impact
    tool_names = [call.tool_name for call in run.tool_calls]
    assert "fetch_metrics" in tool_names
    assert all(call.success for call in run.tool_calls)


def test_broken_agent_raises_when_fail_rate_one():
    with pytest.raises(RuntimeError, match="simulated"):
        BrokenAgent(fail_rate=1.0).run("demo")


def test_broken_agent_violates_guards_when_not_failing():
    run = BrokenAgent(fail_rate=0.0).run("demo")
    assert run.status == "completed"
    tool_names = [call.tool_name for call in run.tool_calls]
    assert "execute_campaign_change" in tool_names
    rec = run.recommendations[0]
    assert rec.requires_approval is False
    assert "execute_campaign_change" in rec.proposed_action
    assert rec.evidence[0].source == "hallucinated"


def test_fixture_factories():
    from fixtures import build_broken, build_reliable

    assert set(build_reliable().keys()) == {"reliable"}
    assert set(build_broken().keys()) == {"broken"}
