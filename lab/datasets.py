"""Dataset loading and validation for the seven labeled evaluation suites.

The lab ships seven dataset categories, one per evaluation dimension:

1. ``factual_accuracy``   - does the agent cite real evidence for its claims?
2. ``tool_use``           - does the agent call the expected tools and avoid
                            forbidden (write) tools without approval?
3. ``recommendation_quality`` - are recommendations complete and evidence-backed?
4. ``prompt_injection``   - do adversarial inputs fail to trigger write actions?
5. ``cost``               - does a run stay within the cost cap?
6. ``latency``            - does a run stay within the latency budget?
7. ``reliability``        - does the agent complete without errors repeatedly?

All datasets are JSON files in ``evaluation/datasets/`` and follow the same
schema conventions as the flagship Growth OS evaluation suite.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class DatasetLoadError(Exception):
    """Raised when a labeled dataset is missing or malformed."""


DATASET_NAMES: tuple[str, ...] = (
    "factual_accuracy",
    "tool_use",
    "recommendation_quality",
    "prompt_injection",
    "cost",
    "latency",
    "reliability",
)


def dataset_names() -> tuple[str, ...]:
    """Return the canonical list of labeled dataset categories."""
    return DATASET_NAMES


@dataclass(frozen=True)
class LabDataset:
    """A single labeled evaluation dataset."""

    name: str
    data: dict[str, Any]

    def require(self, key: str, *, container: str | None = None) -> Any:
        """Fetch a required key or raise a descriptive error."""
        scope = container or self.name
        if key not in self.data:
            raise DatasetLoadError(f"dataset '{scope}' is missing required key '{key}'")
        return self.data[key]

    def cases(self, key: str = "cases") -> list[dict[str, Any]]:
        """Return the labeled cases list, validating shape."""
        value = self.require(key)
        if not isinstance(value, list):
            raise DatasetLoadError(f"dataset '{self.name}' key '{key}' must be a list")
        return value


@dataclass(frozen=True)
class LabDatasets:
    """All seven labeled suites loaded from an evaluation/datasets directory."""

    factual_accuracy: LabDataset
    tool_use: LabDataset
    recommendation_quality: LabDataset
    prompt_injection: LabDataset
    cost: LabDataset
    latency: LabDataset
    reliability: LabDataset

    def as_dict(self) -> dict[str, LabDataset]:
        return {
            "factual_accuracy": self.factual_accuracy,
            "tool_use": self.tool_use,
            "recommendation_quality": self.recommendation_quality,
            "prompt_injection": self.prompt_injection,
            "cost": self.cost,
            "latency": self.latency,
            "reliability": self.reliability,
        }


def _load_one(path: Path) -> LabDataset:
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError as exc:
        raise DatasetLoadError(f"dataset file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DatasetLoadError(f"dataset file is not valid JSON: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise DatasetLoadError(f"dataset file must contain a JSON object: {path}")
    return LabDataset(name=path.stem, data=data)


def load_datasets(datasets_dir: str | Path) -> LabDatasets:
    """Load and validate all seven labeled datasets from a directory."""
    base = Path(datasets_dir)
    if not base.is_dir():
        raise DatasetLoadError(f"datasets directory not found: {base}")

    loaded: dict[str, LabDataset] = {}
    for name in DATASET_NAMES:
        path = base / f"{name}.json"
        loaded[name] = _load_one(path)

    return LabDatasets(
        factual_accuracy=loaded["factual_accuracy"],
        tool_use=loaded["tool_use"],
        recommendation_quality=loaded["recommendation_quality"],
        prompt_injection=loaded["prompt_injection"],
        cost=loaded["cost"],
        latency=loaded["latency"],
        reliability=loaded["reliability"],
    )
