"""HTML dashboard rendering for lab evaluation reports.

``render_dashboard`` produces a self-contained HTML page (inline CSS, no
external assets) with metric cards, a pass/fail table, per-suite detail, and
the agent list. CI artifacts and local report directories both use it.
"""

from __future__ import annotations

import html

from lab.harness import LabReport
from lab.reporters import DEFAULT_THRESHOLDS

_ROW_ORDER: tuple[str, ...] = (
    "accuracy",
    "precision",
    "recall",
    "f1",
    "calibration",
    "factual_accuracy",
    "tool_use_success",
    "recommendation_quality",
    "prompt_injection_resistance",
    "cost_control",
    "latency_budget",
    "reliability",
)

_CSS = """
:root { --bg:#0f172a; --card:#1e293b; --text:#e2e8f0; --muted:#94a3b8; --ok:#34d399; --bad:#f87171; }
* { box-sizing: border-box; }
body {
  margin:0;
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  background:var(--bg); color:var(--text); padding:24px;
}
.wrap { max-width: 960px; margin: 0 auto; }
h1 { font-size: 1.5rem; margin: 0 0 4px; }
h2 {
  font-size: 1.1rem; margin: 28px 0 10px; color: var(--muted);
  text-transform: uppercase; letter-spacing: .05em;
}
.sub { color: var(--muted); margin-bottom: 20px; }
.meta { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 24px; }
.chip {
  background: var(--card); border: 1px solid #334155; border-radius: 999px;
  padding: 4px 12px; font-size: .8rem; color: var(--muted);
}
.verdict { display: inline-block; padding: 6px 14px; border-radius: 8px; font-weight: 700; }
.verdict.pass { background: rgba(52,211,153,.15); color: var(--ok); }
.verdict.fail { background: rgba(248,113,113,.15); color: var(--bad); }
table {
  width: 100%; border-collapse: collapse; background: var(--card);
  border-radius: 12px; overflow: hidden;
}
th, td { text-align: left; padding: 10px 14px; border-bottom: 1px solid #334155; }
th { color: var(--muted); font-weight: 600; font-size: .8rem; text-transform: uppercase; }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
.badge { padding: 2px 8px; border-radius: 6px; font-size: .75rem; font-weight: 600; }
.badge.ok { background: rgba(52,211,153,.15); color: var(--ok); }
.badge.bad { background: rgba(248,113,113,.15); color: var(--bad); }
ul.details { list-style: none; padding: 0; margin: 0; }
ul.details li { padding: 8px 0; border-bottom: 1px solid #334155; color: var(--muted); }
ul.details li strong { color: var(--text); }
"""


def _bar(value: float) -> str:
    pct = max(0.0, min(1.0, value)) * 100
    color = "#34d399" if value >= 0.8 else "#f87171"
    return (
        f'<div style="background:#334155;border-radius:6px;height:8px;width:120px;'
        f'overflow:hidden"><div style="background:{color};width:{pct:.0f}%;height:100%"></div></div>'
    )


def render_dashboard(report: LabReport) -> str:
    """Render a self-contained HTML dashboard for a LabReport."""
    passed = all(report.score(metric) >= DEFAULT_THRESHOLDS.get(metric, 0.0) for metric in report.metrics)
    verdict = '<span class="verdict pass">PASS</span>' if passed else '<span class="verdict fail">FAIL</span>'
    agent_chips = "".join(f'<span class="chip">{html.escape(a)}</span>' for a in report.agent_names)
    rows: list[str] = []
    for metric in _ROW_ORDER:
        if metric not in report.metrics:
            continue
        score = report.metrics[metric]
        threshold = DEFAULT_THRESHOLDS.get(metric)
        ok = threshold is None or score >= threshold
        rows.append(
            "<tr>"
            f"<td>{metric}</td>"
            f"<td class='num'>{score:.3f}</td>"
            f"<td>{_bar(score)}</td>"
            f"<td class='num'>{'-' if threshold is None else f'{threshold:.2f}'}</td>"
            f"<td><span class='badge {'ok' if ok else 'bad'}'>"
            f"{'PASS' if ok else 'FAIL'}</span></td>"
            "</tr>"
        )
    details = "".join(
        f"<li><strong>{html.escape(key)}</strong>: {html.escape(detail)}</li>"
        for key, detail in sorted(report.details.items())
    )
    summary = "".join(
        f"<span class='chip'>{html.escape(key)}: {value}</span>"
        for key, value in sorted(report.dataset_summary.items())
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lab Evaluation: {html.escape(report.target_name)}</title>
<style>{_CSS}</style>
</head>
<body>
<div class="wrap">
  <h1>Lab Evaluation Report</h1>
  <div class="sub">{html.escape(report.target_name)}</div>
  <div class="meta">
    <span class="chip">generated {html.escape(report.generated_at)}</span>
    <span class="chip">{len(report.agent_names)} agents</span>
    {verdict}
  </div>
  <div class="meta">{agent_chips}</div>
  <h2>Metrics</h2>
  <table>
    <thead>
      <tr>
        <th>Metric</th><th class="num">Score</th><th>Trend</th><th class="num">Threshold</th><th>Status</th>
      </tr>
    </thead>
    <tbody>{"".join(rows)}</tbody>
  </table>
  <h2>Per-suite details</h2>
  <ul class="details">{details}</ul>
  <h2>Dataset sizes</h2>
  <div class="meta">{summary}</div>
</div>
</body>
</html>
"""
