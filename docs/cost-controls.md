# Cost Controls

The lab is designed to run with **zero API cost** in every environment:
local development, Docker, and CI.

## How the lab stays free

1. **Rule-based demo mode only.** The lab never calls a model provider during
   evaluation. Agents under test run in their rule-based demo mode with
   precomputed fixtures, per the shared portfolio cost standard.
2. **Mock provider default.** All harness imports use the shared
   `ProviderFactory` default (`MockProvider`). No API keys are read, no
   network egress is attempted.
3. **Zero-cost assertions.** The cost suite (`cost.json`) labels the expected
   maximum API cost as `$0.00`; `cost_control` fails if any agent run
   reports `api_cost_estimate > 0`.
4. **No secrets in code.** `.env.example` documents environment variables;
   nothing is hardcoded.

## Running without cost

```bash
pip install -e ".[dev]"
python -m evaluation.run        # self-evaluation, offline
python scripts/demo_eval.py     # quick demo
docker compose up               # containerized self-evaluation
```

## Safety standards

- **Human-in-the-loop.** Every agent trace is checked for approval gates;
  write actions without `requires_approval=True` fail recommendation quality
  and tool-use suites.
- **Least privilege.** The prompt-injection suite forbids `execute_campaign_change`,
  `send_email`, `publish_content` and similar write tools on adversarial input.
- **No destructive operations.** The lab only reads datasets, runs agents in
  memory, and writes evaluation artifacts under `evaluation/results/`.
- **Rate and latency caps.** `latency.json` bounds the full evaluation run;
  the reliability suite bounds repeated-run execution cost by design.
- **Audit logging.** Every agent run is recorded as an `AgentRun` with tool
  calls, cost, latency, and status, and appears in the generated reports.

## Configuring your repo's cost ceiling

Override thresholds with `--thresholds thresholds.json`:

```json
{
  "cost_control": 1.0,
  "latency_budget": 1.0
}
```

The lab will still run fully offline; thresholds only change the CI gate.
