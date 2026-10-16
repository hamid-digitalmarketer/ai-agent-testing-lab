# CI Integration

This directory contains everything a downstream portfolio repo needs to be
evaluated by the lab from the first commit.

## What to copy

1. `ci-workflow-template.yml` → copy into `<your-repo>/.github/workflows/lab-eval.yml`
   and replace:
   - `<YOUR_USERNAME>` with your GitHub username,
   - `<YOUR_AGENTS_FACTORY>` with the import spec of your agents factory
     (e.g. `demo.runner:build_agents` for ai-marketing-growth-os).
2. `run_lab_eval.py` → invoke it directly from the checked-out lab
   (`deps/ai-agent-testing-lab/integration/run_lab_eval.py`) as the template
   shows, or copy it into your repo and adapt.

## Contract for your repo

The lab does not care about your internals. It requires only:

- your repo exposes a zero-argument factory (e.g. `demo.runner:build_agents`)
  that returns `dict[str, agent]`;
- each agent has `.name` and `.run(input_summary: str)` returning an
  `AgentRun` (or a dict parseable into one) from `ai_marketing_shared`;
- your agents run in rule-based demo mode (zero API keys) during CI.

## Outputs

The entry point writes three artifacts to `--report-dir`:

| File | Purpose |
| --- | --- |
| `metrics.json` | machine-readable metrics for badges / dashboards |
| `report.md` | human-readable evaluation summary |
| `dashboard.html` | self-contained HTML dashboard |

With `--ci-summary`, the Markdown report is also appended to
`$GITHUB_STEP_SUMMARY` so it shows up directly in the workflow run page.

## Exit codes

- `0` — all metrics pass their thresholds;
- `1` — at least one metric failed (job fails, CI is red);
- `2` — the lab could not load datasets / target (configuration error).
