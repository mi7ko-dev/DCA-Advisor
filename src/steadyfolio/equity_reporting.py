"""Human-readable reports for equity and portfolio-policy reviews."""

from __future__ import annotations

from .equity_models import EquityReviewResult
from .models import decimal_to_string
from .portfolio_policy import PortfolioPolicyResult


def _cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _decimal(value) -> str:
    return "N/A" if value is None else decimal_to_string(value)


def _percent(value) -> str:
    return "N/A" if value is None else f"{decimal_to_string(value * 100)}%"


def render_equity_review_report(
    result: EquityReviewResult,
    *,
    title: str = "SteadyFolio Equity Review",
) -> str:
    """Render transparent criteria separately from valuation and limitations."""

    criteria = [
        "| Criterion | Status | Points | Maximum | Observed | Rationale |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    criteria.extend(
        f"| {_cell(item.criterion)} | {item.status} | {_decimal(item.points_awarded)} "
        f"| {_decimal(item.maximum_points)} | {_cell(item.observed_value or 'N/A')} "
        f"| {_cell(item.rationale)} |"
        for item in result.criteria
    )
    if not result.criteria:
        criteria.append("| Not scored | unavailable | 0 | 0 | N/A | Hard screen did not pass |")

    sources = [
        "| Source | Provider | As of | Retrieved | Freshness |",
        "| --- | --- | --- | --- | --- |",
    ]
    sources.extend(
        f"| {_cell(item.source_id)} | {_cell(item.provider)} | {item.as_of} "
        f"| {item.retrieved_at} | {item.freshness} |"
        for item in result.source_assessments
    )

    return "\n".join(
        [
            f"# {title}",
            "",
            f"Instrument: `{result.instrument_id}`",
            f"As of: {result.as_of}",
            f"Identity: `{result.identity_status}`",
            f"Hard screen: `{result.hard_screen_status}`",
            f"Circle of competence: `{result.circle_of_competence.status}`",
            f"Quality model: `{result.quality_model}`",
            "",
            "## Quality score",
            "",
            *criteria,
            "",
            f"Score: {_decimal(result.score_percent)}% "
            f"({_decimal(result.points_awarded)} of "
            f"{_decimal(result.points_available)} available points).",
            f"Completeness: {result.criteria_available} of {result.criteria_total} criteria.",
            f"Classification: `{result.quality_classification}`.",
            "",
            "## Valuation",
            "",
            f"Status: `{result.valuation.status}`.",
            f"Selected method: `{result.valuation.selected_method or 'none'}`.",
            (
                f"Current price: {_decimal(result.valuation.current_price)} "
                f"{result.valuation.currency or ''}"
            ).rstrip(),
            (
                f"Fair value: {_decimal(result.valuation.fair_value)} "
                f"{result.valuation.currency or ''}"
            ).rstrip(),
            f"Margin of safety: {_percent(result.valuation.margin_of_safety)}.",
            "",
            "## Owner earnings",
            "",
            f"Status: `{result.owner_earnings.status}`.",
            result.owner_earnings.interpretation,
            "",
            "## Sources",
            "",
            *sources,
            "",
            "## Limitations",
            "",
            *([f"- {item}" for item in result.limitations] or ["- None reported."]),
            "",
            "## Conclusion",
            "",
            f"Conclusion: `{result.conclusion}`.",
            *[f"- {item}" for item in result.proposed_next_actions],
            "- This review does not execute a transaction or change portfolio policy.",
            f"- Mutation performed: {'yes' if result.mutation_performed else 'no'}.",
        ]
    )


def render_portfolio_policy_report(
    result: PortfolioPolicyResult,
    *,
    title: str = "SteadyFolio Portfolio Policy Check",
) -> str:
    """Render explicit policy checks without implying a complete net-liquidation base."""

    factor_rows = [
        "| Factor group | Current | Previous | Change | Alert |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    factor_rows.extend(
        f"| {_cell(item.id)} | {_decimal(item.current_weight)} "
        f"| {_decimal(item.previous_reported_weight)} | {_decimal(item.change)} "
        f"| {'yes' if item.change_alert else 'no'} |"
        for item in result.factor_groups
    )
    return "\n".join(
        [
            f"# {title}",
            "",
            f"Policy: `{result.policy_id}` version `{result.policy_version}`",
            f"Analysis: `{result.analysis_id}`",
            f"Analysis base: `{result.analysis_base}`",
            "",
            f"Direct-weight breaches: {', '.join(result.direct_weight_breaches) or 'None'}.",
            f"Fragmented positions: {', '.join(result.fragmented_instrument_ids) or 'None'}.",
            "Fragmentation limit breached: "
            f"{'yes' if result.fragmentation_limit_breached else 'no'}.",
            f"Satellite weight: {_decimal(result.satellite_weight)}.",
            f"Satellite limit breached: {'yes' if result.satellite_limit_breached else 'no'}.",
            "",
            "## Factor groups",
            "",
            *factor_rows,
            "",
            "## Limitations",
            "",
            *[f"- {item}" for item in result.warnings],
            f"- Mutation performed: {'yes' if result.mutation_performed else 'no'}.",
        ]
    )
