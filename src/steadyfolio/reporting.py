"""English Markdown rendering for deterministic structured results."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from .models import AnalysisResult, ContributionPlan, PortfolioState


def _money(value: Decimal, currency: str) -> str:
    return f"{value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,.2f} {currency}"


def _percent(value: Decimal) -> str:
    return f"{(value * Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}%"


def render_analysis_report(state: PortfolioState, analysis: AnalysisResult) -> str:
    names = {instrument.id: instrument.name for instrument in state.instruments}
    rows = [
        "| Instrument | Value | Current weight | Approved target | Drift |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for position in analysis.positions:
        rows.append(
            "| {name} | {value} | {current} | {target} | {drift} |".format(
                name=names[position.instrument_id],
                value=_money(position.current_value, analysis.base_currency),
                current=_percent(position.current_weight),
                target=_percent(position.target_weight),
                drift=_percent(position.drift),
            )
        )

    warnings = (
        "\n".join(f"- {warning}" for warning in analysis.warnings)
        if analysis.warnings
        else "- None."
    )
    sources = ", ".join(f"`{source}`" for source in analysis.source_ids) or "None"
    return "\n".join(
        [
            "# Synthetic Portfolio Analysis",
            "",
            f"Valuation date: {analysis.valuation_date}",
            f"Base currency: {analysis.base_currency}",
            f"Portfolio value: {_money(analysis.total_value, analysis.base_currency)}",
            "",
            *rows,
            "",
            "## Directly observable indicators",
            "",
            f"- Weighted annual fee rate: {_percent(analysis.weighted_annual_fee_rate)}",
            f"- Maximum direct position weight: {_percent(analysis.maximum_direct_weight)}",
            f"- Herfindahl index: {analysis.herfindahl_index:.4f}",
            "",
            "## Warnings",
            "",
            warnings,
            "",
            "## Provenance and limitations",
            "",
            f"- Source records: {sources}",
            f"- Calculation version: `{analysis.calculation_version}`",
            "- Trading currency and economic exposure are separate concepts.",
            "- This deterministic analysis is not a forecast or financial advice.",
        ]
    )


def render_contribution_report(
    state: PortfolioState,
    analysis: AnalysisResult,
    plan: ContributionPlan,
) -> str:
    names = {instrument.id: instrument.name for instrument in state.instruments}
    rows = [
        "| Instrument | Current | Target | Drift | Quantity | Purchase | Cost | Expected post-weight | Remaining drift |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for line in plan.lines:
        rows.append(
            "| {name} | {current} | {target} | {drift} | {quantity} | {purchase} | {cost} | {post} | {remaining} |".format(
                name=names[line.instrument_id],
                current=_percent(line.current_weight),
                target=_percent(line.target_weight),
                drift=_percent(line.drift),
                quantity=format(line.quantity, "f"),
                purchase=_money(line.proposed_contribution, plan.currency),
                cost=_money(line.estimated_trade_cost, plan.currency),
                post=_percent(line.expected_post_contribution_weight),
                remaining=_percent(line.remaining_drift),
            )
        )

    warnings = (
        "\n".join(f"- {warning}" for warning in plan.warnings)
        if plan.warnings
        else "- None."
    )
    sources = ", ".join(f"`{source}`" for source in plan.source_ids) or "None"
    return "\n".join(
        [
            "# Synthetic Monthly Contribution Plan",
            "",
            f"Method: `{plan.method}`",
            f"Valuation date: {plan.valuation_date}",
            f"Available contribution: {_money(plan.contribution_amount, plan.currency)}",
            f"Starting portfolio value: {_money(analysis.total_value, plan.currency)}",
            "",
            *rows,
            "",
            "## Reconciliation",
            "",
            f"- Purchases: {_money(plan.total_purchase_value, plan.currency)}",
            f"- Estimated trade costs: {_money(plan.total_estimated_trade_cost, plan.currency)}",
            f"- Remaining cash: {_money(plan.remaining_cash, plan.currency)}",
            f"- Expected post-contribution value: {_money(plan.expected_post_contribution_value, plan.currency)}",
            "",
            "Purchases plus estimated costs plus remaining cash equal the available contribution.",
            "Residual cash is retained and included in the expected post-contribution value; fees reduce that value.",
            "No sale or executed transaction is created by this proposal.",
            "",
            "## Warnings",
            "",
            warnings,
            "",
            "## Provenance and limitations",
            "",
            f"- Source records: {sources}",
            f"- Calculation version: `{plan.calculation_version}`",
            "- Prices, FX rates, fees, and fractional-share settings are synthetic assumptions.",
            "- This scenario is not a forecast or financial advice.",
        ]
    )
