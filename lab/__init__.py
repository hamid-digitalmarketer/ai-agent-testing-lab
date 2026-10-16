"""ai-agent-testing-lab: reusable reliability and evaluation lab.

Every repository in the AI marketing portfolio ships labeled datasets and a
rule-based demo mode. This package provides the shared harness, metrics,
reporters, and dashboards that evaluate those agents uniformly from CI.
"""

from __future__ import annotations

from lab.datasets import (
    DatasetLoadError,
    LabDataset,
    LabDatasets,
    dataset_names,
    load_datasets,
)
from lab.harness import AgentLoadError, LabReport, TargetLoader, TestHarness
from lab.metrics import (
    calibration_error,
    classification_metrics,
    cost_control,
    factual_accuracy,
    latency_budget,
    prompt_injection_resistance,
    recommendation_quality,
    reliability,
    tool_use_success,
)

__version__ = "0.1.0"

__all__ = [
    "AgentLoadError",
    "DatasetLoadError",
    "LabDataset",
    "LabDatasets",
    "LabReport",
    "TargetLoader",
    "TestHarness",
    "calibration_error",
    "classification_metrics",
    "cost_control",
    "dataset_names",
    "factual_accuracy",
    "latency_budget",
    "load_datasets",
    "prompt_injection_resistance",
    "recommendation_quality",
    "reliability",
    "tool_use_success",
]
