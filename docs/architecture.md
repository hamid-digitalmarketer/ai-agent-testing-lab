# Architecture

ai-agent-testing-lab is a reusable evaluation and reliability lab for every
AI marketing portfolio repository. It follows the shared portfolio standards
(evidence over opinion, structured outputs, human-in-the-loop, observability,
evaluation, cost controls) and is designed to be imported by other repos from
day one.

## Goals

1. Give every repo one canonical evaluation suite with the same seven labeled
   datasets and the same pass thresholds.
2. Make evaluation a first-class CI citizen: a repo that fails any threshold
   cannot merge.
3. Prove the lab itself works by reproducing known agent failures (the
   lab's own evaluation).

## Repository layout

```
ai-agent-testing-lab/
+-- lab/                  # Reusable lab package
│   +-- datasets.py       # Seven labeled dataset loaders (JSON)
│   +-- harness.py        # TargetLoader + TestHarness (agent evaluation loop)
│   +-- metrics.py        # Metric functions for all seven suites
│   +-- reporters.py      # JSON / Markdown / GitHub Actions reporters
│   +-- dashboard.py      # Self-contained HTML dashboard renderer
│   +-- integration.py    # run_lab_eval entry point for CI
│   +-- cli.py            # lab-eval command line interface
+-- fixtures/             # Known-good and known-broken agents (self-eval)
+-- evaluation/
│   +-- datasets/         # Seven labeled datasets (factual, tool, quality,
│   │                     # injection, cost, latency, reliability)
│   +-- run.py            # Self-evaluation runner
│   +-- results/          # Generated reports (gitignored)
+-- integration/          # CI templates + entry script for other repos
+-- infra/                # Dockerfile + docker-compose.yml
+-- scripts/              # Local demo helpers
+-- tests/                # Unit tests (coverage > 80% on lab + fixtures)
```

## Core design decisions

### 1. Datasets are JSON contracts, not code

Each of the seven datasets is a plain JSON file in `evaluation/datasets/`.
The loaders in `lab/datasets.py` read them into `LabDataset` objects with a
stable `cases()` accessor. Downstream repos can swap in their own datasets by
pointing `--datasets` at their own directory; the harness never assumes a
specific marketing domain.

### 2. Agents are duck-typed

The harness does not import your code. It receives a factory import spec
(`module:callable`, e.g. `demo.runner:build_agents`) and calls it to obtain
`dict[str, agent]`. Every agent must expose:

- `name: str`
- `run(input_summary: str) -> AgentRun` (the shared Pydantic schema, or a
  dict parseable into it)

This keeps the lab provider-agnostic and makes integration a copy-paste.

### 3. One evaluation loop, seven metric families

`TestHarness.evaluate` runs each agent once per labeled case and derives:

| Suite | Metric | What it measures |
| --- | --- | --- |
| Factual accuracy | `factual_accuracy` | Cited evidence metric/value matches the label |
| Tool-use success | `tool_use_success` | Expected tools called; forbidden tools never called |
| Recommendation quality | `recommendation_quality` | Complete, evidence-backed, approval-gated recs |
| Prompt-injection resistance | `prompt_injection_resistance` | Adversarial inputs never trigger write tools |
| Cost control | `cost_control` | Zero API cost in rule-based demo mode |
| Latency budget | `latency_budget` | Whole-run latency within budget |
| Reliability | `reliability` | Repeated runs complete without errors |

Secondary metrics (`accuracy`, `precision`, `recall`, `f1`, `calibration`)
are computed from the binary classifications produced by the primary suites.

### 4. Reports are artifacts, thresholds gate CI

`lab.reporters.write_reports` emits `metrics.json` (machines), `report.md`
(humans), and `dashboard.html` (visual). `integration.run_lab_eval` returns
an exit code that CI turns into a red/green gate. `--ci-summary` appends the
Markdown report to `$GITHUB_STEP_SUMMARY`.

### 5. The lab evaluates itself

`fixtures/` ships a deliberately broken agent (hallucinated evidence,
forbidden write call, no approval gate, 50% crash rate) and a known-good
agent. `evaluation/run.py` asserts the good agent passes while the broken one
fails every failure-sensitive suite — reproducing known failures is the lab's
own definition of done.

## Trade-offs

- **JSON datasets over a DSL**: easy to inspect, easy to extend, zero code to
  learn. Complex programmatic labels can be added later via custom loaders.
- **Duck-typed agents over ABCs**: keeps the lab decoupled from repo internals;
  a tiny shared-schema dependency (`ai-marketing-shared`) provides the types.
- **Rule-based fixtures over live models**: evaluation must run in CI with
  zero API keys; probabilistic model behavior is outside the lab's gate.
