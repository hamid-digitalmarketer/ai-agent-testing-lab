# Changelog

All notable changes to ai-agent-testing-lab follow [Keep a Changelog](https://keepachangelog.com/) and [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-10-16

### Added

- Test harness (`lab/harness.py`) that imports agent factories from any
  portfolio repo via `TargetLoader` and runs the full evaluation.
- Seven labeled datasets under `evaluation/datasets/`: factual accuracy,
  tool-use, recommendation quality, prompt-injection resistance, cost,
  latency, and reliability.
- Metrics module (`lab/metrics.py`) covering accuracy, precision/recall/F1,
  calibration, tool-use success, recommendation quality, injection
  resistance, cost control, latency budget, and reliability.
- Reporters (`lab/reporters.py`) emitting JSON, Markdown, and GitHub Actions
  step-summary output, plus a self-contained HTML dashboard
  (`lab/dashboard.py`).
- Integration helper (`integration/run_lab_eval.py`) and reusable CI workflow
  template (`integration/ci-workflow-template.yml`) for downstream repos.
- Self-evaluation (`evaluation/run.py`) that proves lab effectiveness by
  reproducing known agent failures with the `ReliableAgent` / `BrokenAgent`
  fixtures.
- CLI entry point `lab-eval` (`lab/cli.py`).
- Docker support (`infra/Dockerfile`, `infra/docker-compose.yml`), CI pipeline
  (`.github/workflows/ci.yml`) with ruff + mypy + pytest + self-evaluation +
  docker build.
- Full documentation: README, architecture, evaluation, cost-controls,
  contributing guide, MIT license, environment template.
