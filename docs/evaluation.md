# Evaluation

This document describes the lab's evaluation methodology, the seven labeled
datasets, the metrics reporters, and current results.

## Methodology

Every agent under test is evaluated against seven labeled dataset families.
Each dataset is a JSON contract with explicit labels; the harness converts
agent traces into binary outcomes, aggregates them into metrics, and compares
them against pass thresholds.

### The seven suites

| Suite | Dataset | Label source | Pass threshold (default) |
| --- | --- | --- | --- |
| Factual accuracy | `factual_accuracy.json` | expected evidence metric + value range per case | 0.80 |
| Tool-use success | `tool_use.json` | required tools per agent + global forbidden tools | 0.80 |
| Recommendation quality | `recommendation_quality.json` | required fields, min evidence, approval gate | 0.80 |
| Prompt-injection resistance | `prompt_injection.json` | adversarial inputs; forbidden write tools | 0.90 |
| Cost control | `cost.json` | max API cost USD (0 for demo mode) | 1.00 |
| Latency budget | `latency.json` | max latency for the full run | 1.00 |
| Reliability | `reliability.json` | min success rate over repeated runs | 0.90 |

### Metrics reported

Primary suite scores plus:

- `accuracy`, `precision`, `recall`, `f1` — aggregate binary classification
  across factual / tool / quality / injection outcomes;
- `calibration` — confidence vs. correctness agreement (reported, not gated).

## Running

```bash
# Full self-evaluation (fixtures)
python -m evaluation.run

# Evaluate any installed repo via the CI entry point
python integration/run_lab_eval.py --target demo.runner:build_agents \
    --datasets evaluation/datasets --report-dir evaluation/results --ci-summary

# Or via the packaged CLI
lab-eval --target demo.runner:build_agents
```

## Current results (self-evaluation)

The lab's effectiveness is proven by reproducing known failures:

| Suite | Reliable agent | Broken agent |
| --- | ---: | ---: |
| factual_accuracy | 1.00 | 0.00 |
| tool_use_success | 1.00 | 0.00 |
| recommendation_quality | 1.00 | 0.00 |
| prompt_injection_resistance | 1.00 | 0.00 |
| cost_control | 1.00 | 1.00 |
| latency_budget | 1.00 | 1.00 |
| reliability | 1.00 | ~0.50 |

`evaluation/run.py` fails the lab itself unless: the reliable agent passes
all thresholds **and** the broken agent fails all failure-sensitive suites.
Run `python -m evaluation.run` after every lab change to confirm the lab still
detects the failures it was built to catch.

## Adding a repo

See `integration/README.md`. In short: expose a factory returning
`dict[str, agent]`, copy the workflow template, and every push is evaluated.
