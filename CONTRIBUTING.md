# Contributing to ai-agent-testing-lab

Thanks for helping make the lab more reliable. Please keep these guidelines in
mind.

## Setup

```bash
pip install -e ".[dev]"
pip install -e ../ai-marketing-shared
```

## Development loop

```bash
ruff check .          # lint
mypy lab fixtures evaluation scripts   # type check
pytest                # tests + coverage (must stay above 80%)
python -m evaluation.run   # self-evaluation must stay effective
```

All checks must pass before opening a PR.

## Adding a labeled case

1. Open the matching file under `evaluation/datasets/`.
2. Add a case that reflects a real, observable agent behavior.
3. If the case targets a specific repo, name the agent field explicitly.
4. Run `pytest tests/test_datasets.py` to make sure the dataset still loads.

## Adding a metric

1. Implement the metric function in `lab/metrics.py` with a docstring that
   states exactly what a score of 1.0 and 0.0 mean.
2. Wire it into `TestHarness.evaluate()` in `lab/harness.py`.
3. Add the metric to the default thresholds in `lab/reporters.py` if CI should
   enforce it.
4. Add unit tests in `tests/test_metrics.py` and, if relevant, a harness test.

## Commit style

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` new datasets, metrics, or integration features
- `fix:` bug fixes in the harness or reporters
- `test:` new or updated tests
- `docs:` documentation changes
- `chore:` tooling, CI, or packaging changes

## Code of conduct

Be respectful. The lab is a shared asset for the whole portfolio; prefer
backwards-compatible changes and deprecation over breaking edits.
