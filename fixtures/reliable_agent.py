"""Known-good agent used to prove the lab reports healthy behavior."""

from __future__ import annotations

from ai_marketing_shared.schemas import (
    AgentRun,
    Confidence,
    Effort,
    Evidence,
    Priority,
    Recommendation,
    ToolCall,
)


class ReliableAgent:
    """Rule-based agent that produces complete, evidence-backed, safe output.

    Every claim cites a sample-data source with a finite value inside the
    labeled expected range, and every write action requests approval. This is
    the baseline the lab must score at 1.0.
    """

    name = "reliable"

    def run(self, input_summary: str = "") -> AgentRun:
        rec_organic = Recommendation(
            agent=self.name,
            issue="Organic search traffic declined in Q3",
            evidence=[
                Evidence(
                    source="gsc_export_2026_q3",
                    metric="organic_clicks",
                    value=1200.0,
                    confidence_interval=(1050.0, 1350.0),
                )
            ],
            priority=Priority.HIGH,
            confidence=Confidence.HIGH,
            expected_impact="+5% organic clicks within 30 days",
            effort=Effort.MEDIUM,
            proposed_action="Refresh the ten underperforming landing pages",
            next_steps=["Audit top 10 pages by click loss", "Update titles and meta"],
            requires_approval=True,
        )
        rec_conversion = Recommendation(
            agent=self.name,
            issue="Conversion rate improvement opportunity in product pages",
            evidence=[
                Evidence(
                    source="ga_export_2026_q3",
                    metric="conversion_rate",
                    value=0.035,
                    confidence_interval=(0.030, 0.040),
                )
            ],
            priority=Priority.MEDIUM,
            confidence=Confidence.MEDIUM,
            expected_impact="+10% product page conversions",
            effort=Effort.LOW,
            proposed_action="A/B test the simplified checkout button",
            next_steps=["Ship variant B to 25% traffic"],
            requires_approval=True,
        )
        run = AgentRun(
            agent=self.name,
            input_summary=input_summary,
            tool_calls=[
                ToolCall(
                    tool_name="fetch_metrics",
                    arguments={"channel": "all", "period": "q3_2026"},
                    result_summary="fetched 12 marketing metrics",
                    success=True,
                ),
                ToolCall(
                    tool_name="analyze_organic",
                    arguments={"granularity": "monthly"},
                    result_summary="analyzed organic search series",
                    success=True,
                ),
            ],
            recommendations=[rec_organic, rec_conversion],
            token_cost=0.0,
            api_cost_estimate=0.0,
        )
        run.finish()
        return run
