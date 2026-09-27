"""English Markdown reports for Phase 4 structured results."""

from __future__ import annotations

from decimal import Decimal

from .models import PortfolioState
from .research_models import PortfolioIntelligenceResult, ThesisReviewResult


def _percent(value: Decimal | None) -> str:
    return "n/a" if value is None else f"{value * Decimal('100'):.2f}%"


def _value(value: Decimal | None, currency: str | None = None) -> str:
    if value is None:
        return "n/a"
    suffix = f" {currency}" if currency else ""
    return f"{value:,.2f}{suffix}"


def render_intelligence_report(
    state: PortfolioState, result: PortfolioIntelligenceResult
) -> str:
    """Render a concise report without converting missing coverage to zero."""

    names = {instrument.id: instrument.name for instrument in state.instruments}
    lines = [
        "# Synthetic Portfolio Intelligence Report",
        "",
        f"Analysis date: {result.analysis_date}",
        f"Base currency: {result.base_currency}",
        "",
        "## Instrument facts",
        "",
        "| Instrument | Type | Domicile | Distribution | Index | Replication | TER | Fund size | Facts as of |",
        "| --- | --- | --- | --- | --- | --- | ---: | ---: | --- |",
    ]
    for item in result.instrument_summaries:
        lines.append(
            "| "
            + " | ".join(
                [
                    item.name,
                    item.kind,
                    item.domicile or "unavailable",
                    item.distribution_policy or "unavailable",
                    item.index_name or "unavailable",
                    item.replication_method or "unavailable",
                    _percent(item.ter),
                    _value(item.fund_size, item.fund_size_currency),
                    item.facts_as_of or "unavailable",
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Observed holdings overlap",
            "",
            "| Pair | Observed overlap | Left coverage | Right coverage | Holdings as of |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
    )
    if result.overlaps:
        for item in result.overlaps:
            lines.append(
                f"| {names[item.left_instrument_id]} / {names[item.right_instrument_id]} "
                f"| {_percent(item.observed_overlap_weight)} "
                f"| {_percent(item.left_holdings_coverage)} "
                f"| {_percent(item.right_holdings_coverage)} "
                f"| {', '.join(item.holdings_as_of_dates) or 'unavailable'} |"
            )
    else:
        lines.append("| No comparable ETF pair | n/a | n/a | n/a | n/a |")

    concentration = result.company_concentration
    lines.extend(
        [
            "",
            "## Observed company or issuer concentration",
            "",
            f"Covered portfolio weight: {_percent(concentration.covered_portfolio_weight)}",
            f"Unclassified portfolio weight: {_percent(concentration.unclassified_portfolio_weight)}",
            "",
            "| Entity | Observed portfolio weight |",
            "| --- | ---: |",
        ]
    )
    for item in concentration.exposures:
        lines.append(f"| {item.name} | {_percent(item.observed_portfolio_weight)} |")

    lines.extend(["", "## Classified exposures", ""])
    for exposure in result.exposures:
        lines.extend(
            [
                f"### {exposure.dimension.capitalize()}",
                "",
                f"Coverage: {_percent(exposure.covered_portfolio_weight)}; "
                f"unclassified: {_percent(exposure.unclassified_portfolio_weight)}",
                "",
                "| Classification | Observed portfolio weight |",
                "| --- | ---: |",
            ]
        )
        for item in exposure.entries:
            lines.append(f"| {item.label} | {_percent(item.observed_portfolio_weight)} |")
        lines.append("")

    lines.extend(
        [
            "## Historical metrics",
            "",
            "| Instrument | Period | Total return | Annualized volatility | Maximum drawdown | Benchmark excess | Convention |",
            "| --- | --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for metric in result.historical_metrics:
        lines.append(
            f"| {names[metric.instrument_id]} "
            f"| {metric.start_date} to {metric.end_date} "
            f"| {_percent(metric.cumulative_return)} "
            f"| {_percent(metric.annualized_volatility)} "
            f"| {_percent(metric.maximum_drawdown)} "
            f"| {_percent(metric.excess_return)} "
            f"| {metric.frequency} {metric.return_convention}, distributions "
            f"{metric.distribution_treatment}, corporate actions "
            f"{metric.corporate_action_treatment} |"
        )

    lines.extend(["", "## Correlation", ""])
    if result.correlations:
        for item in result.correlations:
            lines.append(
                f"- {names[item.left_instrument_id]} / {names[item.right_instrument_id]}: "
                f"{item.correlation:.4f} over {item.return_observation_count} aligned returns."
            )
    else:
        lines.append("- No supported pairwise correlation was available.")

    lines.extend(["", "## Stress windows", ""])
    if result.stress_metrics:
        for item in result.stress_metrics:
            lines.append(
                f"- {item.stress_name} — {names[item.instrument_id]}: "
                f"return {_percent(item.cumulative_return)}, maximum drawdown "
                f"{_percent(item.maximum_drawdown)} ({item.start_date} to {item.end_date})."
            )
    else:
        lines.append("- No stress window had sufficient observations.")

    lines.extend(["", "## Source freshness and permissions", ""])
    for source in result.source_assessments:
        lines.append(
            f"- `{source.source_id}`: {source.provider}; as of {source.as_of}; "
            f"retrieved {source.retrieved_at}; {source.freshness} ({source.age_days} days); "
            f"cache permitted={str(source.cache_permitted).lower()}; "
            f"redistribution permitted={str(source.redistribution_permitted).lower()}; "
            f"terms `{source.terms_reference}`."
        )

    lines.extend(["", "## Warnings and limitations", ""])
    for warning in result.warnings:
        lines.append(f"- {warning}")
    lines.extend(
        [
            "- Top-holdings data is partial and is not presented as complete look-through coverage.",
            "- Historical metrics and stress windows describe synthetic past observations; they are not forecasts.",
            "- No policy, holding, or transaction was changed by this analysis.",
            "- This synthetic report is not financial advice.",
            "",
        ]
    )
    return "\n".join(lines)


def render_thesis_review_report(
    state: PortfolioState, review: ThesisReviewResult
) -> str:
    """Render facts and interpretation as visibly separate sections."""

    names = {instrument.id: instrument.name for instrument in state.instruments}
    lines = [
        "# Synthetic Investment Thesis Review",
        "",
        f"Instrument: {names[review.instrument_id]}",
        f"Reviewed at: {review.reviewed_at}",
        f"Role: {review.role}",
        f"Approved target reference: {_percent(review.target_weight)}",
        f"Target range: {_percent(review.target_range_min)} to {_percent(review.target_range_max)}",
        f"Benchmark: {names.get(review.benchmark_instrument_id, 'unavailable')}",
        f"Last review: {review.last_review_date or 'unavailable'}",
        f"Next review: {review.next_review_date or 'unavailable'}",
        "",
        "## Evidence facts",
        "",
    ]
    lines.extend(f"- {item}" for item in review.evidence_facts)
    lines.extend(["", "## Interpretation", ""])
    lines.extend(f"- {item}" for item in review.interpretations)
    lines.extend(
        [
            "",
            "## Proposed action",
            "",
            f"Action for user review: `{review.proposed_action}`",
        ]
    )
    lines.extend(f"- {item}" for item in review.proposed_changes)
    lines.extend(["", "## Source provenance", ""])
    for source in review.source_assessments:
        lines.append(
            f"- `{source.source_id}`: {source.provider}; as of {source.as_of}; "
            f"retrieved {source.retrieved_at}; {source.freshness} ({source.age_days} days); "
            f"methodology: {source.methodology}"
        )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in review.limitations)
    lines.extend(
        [
            "- A price decline alone is not treated as thesis failure.",
            "- This review does not mutate holdings, transactions, the thesis, or approved policy.",
            "- This synthetic review is not financial advice.",
            "",
        ]
    )
    return "\n".join(lines)
