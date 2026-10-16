"""Lab fixtures: known-good and known-broken agents for the self-evaluation.

The lab proves it works by reproducing known agent failures: a reliable agent
must score well on every suite while a deliberately broken agent must be
caught (low factual accuracy, forbidden write calls, missing approval gates,
and reliability failures). These fixtures implement the same duck-typed
interface the harness expects from any portfolio repo.
"""

from __future__ import annotations

from fixtures.broken_agent import BrokenAgent
from fixtures.reliable_agent import ReliableAgent


def build_reliable() -> dict[str, ReliableAgent]:
    """Factory yielding the known-good agent."""
    return {"reliable": ReliableAgent()}


def build_agents() -> dict[str, ReliableAgent]:
    """Default entry point used when a target spec omits the attribute."""
    return build_reliable()


def build_broken() -> dict[str, BrokenAgent]:
    """Factory yielding the known-broken agent (50% run failure rate)."""
    return {"broken": BrokenAgent(fail_rate=0.5)}


# Malformed factories used by the harness tests to prove validation errors.
# They are intentionally wrong and should never be used as real targets.


def build_none_factory():
    return None


def build_list_factory():
    return ["not", "a", "dict"]


def build_empty_factory():
    return {}


def build_bad_agent_factory():
    return {"bad": object()}


__all__ = [
    "BrokenAgent",
    "ReliableAgent",
    "build_agents",
    "build_bad_agent_factory",
    "build_broken",
    "build_empty_factory",
    "build_list_factory",
    "build_none_factory",
    "build_reliable",
]
