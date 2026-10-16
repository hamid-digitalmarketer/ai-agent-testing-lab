"""Unit tests for lab.datasets."""

from __future__ import annotations

import json

import pytest
from lab.datasets import (
    DATASET_NAMES,
    DatasetLoadError,
    LabDataset,
    dataset_names,
    load_datasets,
)


def test_dataset_names_are_seven(tmp_path):
    assert set(dataset_names()) == {
        "factual_accuracy",
        "tool_use",
        "recommendation_quality",
        "prompt_injection",
        "cost",
        "latency",
        "reliability",
    }
    assert len(DATASET_NAMES) == 7


def _write_all_datasets(root):
    for name in DATASET_NAMES:
        (root / f"{name}.json").write_text(json.dumps({"name": name, "cases": []}), encoding="utf-8")
    return root


def test_load_datasets_loads_all_seven(tmp_path):
    root = _write_all_datasets(tmp_path)
    datasets = load_datasets(root)
    assert datasets.factual_accuracy.name == "factual_accuracy"
    assert datasets.tool_use.name == "tool_use"
    assert set(datasets.as_dict().keys()) == set(DATASET_NAMES)


def test_load_datasets_missing_dir(tmp_path):
    with pytest.raises(DatasetLoadError, match="not found"):
        load_datasets(tmp_path / "nope")


def test_load_datasets_missing_one(tmp_path):
    root = _write_all_datasets(tmp_path)
    (root / "cost.json").unlink()
    with pytest.raises(DatasetLoadError, match="not found"):
        load_datasets(root)


def test_load_datasets_invalid_json(tmp_path):
    root = _write_all_datasets(tmp_path)
    (root / "cost.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(DatasetLoadError, match="not valid JSON"):
        load_datasets(root)


def test_load_datasets_non_object(tmp_path):
    root = _write_all_datasets(tmp_path)
    (root / "cost.json").write_text("[1,2,3]", encoding="utf-8")
    with pytest.raises(DatasetLoadError, match="JSON object"):
        load_datasets(root)


def test_lab_dataset_require_and_cases():
    ds = LabDataset(name="x", data={"cases": [{"id": 1}], "top": "v"})
    assert ds.require("top") == "v"
    assert ds.cases() == [{"id": 1}]
    with pytest.raises(DatasetLoadError, match="missing required key"):
        ds.require("missing")
    with pytest.raises(DatasetLoadError, match="must be a list"):
        LabDataset(name="x", data={"cases": {"id": 1}}).cases()
