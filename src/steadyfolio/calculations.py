"""Pure Decimal-based portfolio analysis and contribution planning."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR, localcontext
import re
from typing import Mapping, Sequence

from .errors import MissingFxRateError, MissingPriceError, ValidationError
from .models import (
    CALCULATION_VERSION,
    AnalysisResult,
    ContributionLine,
    ContributionPlan,
    FxRate,
    Listing,
    MarketPrice,
    PortfolioState,
    PositionAnalysis,
    TargetAllocation,
    TradingConstraint,
)
from .validation import validate_state


_CENT = Decimal("0.01")
_CONCENTRATION_THRESHOLD = Decimal("0.20")
_CURRENCY = re.compile(r"^[A-Z]{3}$")


def _as_date(value: str, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValidationError(f"{field} must be an ISO date.") from error


def _approved_target(state: PortfolioState) -> TargetAllocation:
    approved = tuple(
        allocation
        for allocation in state.target_allocations
        if allocation.status == "approved"
    )
    if len(approved) != 1:
        raise ValidationError("Exactly one approved target allocation is required.")
    return approved[0]


def _latest_prices(
    state: PortfolioState,
    prices: Sequence[MarketPrice],
    valuation_date: str,
) -> dict[str, MarketPrice]:
    cutoff = _as_date(valuation_date, "valuation_date")
    listings = {listing.id: listing for listing in state.listings}
    source_ids = {source.id for source in state.data_sources}
    selected: dict[str, MarketPrice] = {}
    selected_dates: dict[str, date] = {}
    for price in prices:
        listing = listings.get(price.listing_id)
        if listing is None:
            raise ValidationError("A market price references an unknown listing.")
        if price.currency != listing.trading_currency:
            raise ValidationError("A market price currency differs from its listing.")
        if price.amount <= 0 or not price.amount.is_finite():
            raise ValidationError("Market prices must be positive finite decimals.")
        if price.source_id not in source_ids:
            raise ValidationError("A market price references an unknown data source.")
        price_date = _as_date(price.as_of, "prices[].as_of")
        if price_date > cutoff:
            continue
        current_date = selected_dates.get(price.listing_id)
        if current_date is None or price_date > current_date:
            selected[price.listing_id] = price
            selected_dates[price.listing_id] = price_date
    return selected


class _FxTable:
    def __init__(
        self,
        state: PortfolioState,
        rates: Sequence[FxRate],
        valuation_date: str,
    ) -> None:
        cutoff = _as_date(valuation_date, "valuation_date")
        source_ids = {source.id for source in state.data_sources}
        self._rates: dict[tuple[str, str], tuple[date, Decimal, str]] = {}
        for rate in rates:
            if not _CURRENCY.fullmatch(rate.base_currency) or not _CURRENCY.fullmatch(
                rate.quote_currency
            ):
                raise ValidationError("FX currencies must be uppercase ISO 4217 codes.")
            if rate.rate <= 0 or not rate.rate.is_finite():
                raise ValidationError("FX rates must be positive finite decimals.")
            if rate.base_currency == rate.quote_currency:
                raise ValidationError("An FX rate must contain two currencies.")
            if rate.source_id not in source_ids:
                raise ValidationError("An FX rate references an unknown data source.")
            rate_date = _as_date(rate.as_of, "fx_rates[].as_of")
            if rate_date > cutoff:
                continue
            key = (rate.base_currency, rate.quote_currency)
            current = self._rates.get(key)
            if current is None or rate_date > current[0]:
                self._rates[key] = (rate_date, rate.rate, rate.source_id)

    def convert(
        self, amount: Decimal, source_currency: str, target_currency: str
    ) -> tuple[Decimal, str | None]:
        if source_currency == target_currency:
            return amount, None
        direct = self._rates.get((source_currency, target_currency))
        if direct is not None:
            return amount * direct[1], direct[2]
        inverse = self._rates.get((target_currency, source_currency))
        if inverse is not None:
            return amount / inverse[1], inverse[2]
        raise MissingFxRateError(
            f"No dated FX rate for {source_currency}/{target_currency}."
        )


def _position_values(
    state: PortfolioState,
    prices: Sequence[MarketPrice],
    fx_rates: Sequence[FxRate],
    valuation_date: str,
) -> tuple[dict[str, Decimal], set[str]]:
    selected_prices = _latest_prices(state, prices, valuation_date)
    fx_table = _FxTable(state, fx_rates, valuation_date)
    listings = {listing.id: listing for listing in state.listings}
    quantities: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for holding in state.holdings:
        quantities[holding.listing_id] += holding.quantity

    values: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    used_sources: set[str] = set()
    for listing_id, quantity in quantities.items():
        if quantity == 0:
            continue
        listing = listings[listing_id]
        price = selected_prices.get(listing_id)
        if price is None:
            raise MissingPriceError(
                f"No dated market price for held listing {listing_id!r}."
            )
        local_value = quantity * price.amount
        base_value, fx_source = fx_table.convert(
            local_value,
            listing.trading_currency,
            state.investor_profile.base_currency,
        )
        values[listing.instrument_id] += base_value
        used_sources.add(price.source_id)
        if fx_source is not None:
            used_sources.add(fx_source)
    return dict(values), used_sources


def analyze_portfolio(
    state: PortfolioState,
    prices: Sequence[MarketPrice],
    fx_rates: Sequence[FxRate],
    valuation_date: str,
) -> AnalysisResult:
    """Value holdings and calculate weights, signed drift, fees, and concentration."""

    validate_state(state)
    _as_date(valuation_date, "valuation_date")
    approved = _approved_target(state)
    if _as_date(approved.effective_date, "approved_target.effective_date") > _as_date(
        valuation_date, "valuation_date"
    ):
        raise ValidationError("The approved target is not effective on the valuation date.")
    target_weights = {
        target.instrument_id: target.weight for target in approved.targets
    }
    instrument_by_id = {instrument.id: instrument for instrument in state.instruments}

    with localcontext() as context:
        context.prec = 36
        values, used_sources = _position_values(
            state, prices, fx_rates, valuation_date
        )
        total_value = sum(values.values(), Decimal("0"))

        ordered_ids = [target.instrument_id for target in approved.targets]
        ordered_ids.extend(sorted(set(values) - set(ordered_ids)))
        positions: list[PositionAnalysis] = []
        warnings: list[str] = []
        for instrument_id in ordered_ids:
            current_value = values.get(instrument_id, Decimal("0"))
            current_weight = (
                current_value / total_value if total_value > 0 else Decimal("0")
            )
            target_weight = target_weights.get(instrument_id, Decimal("0"))
            positions.append(
                PositionAnalysis(
                    instrument_id=instrument_id,
                    current_value=current_value,
                    current_weight=current_weight,
                    target_weight=target_weight,
                    drift=current_weight - target_weight,
                )
            )
            if instrument_id not in target_weights and current_value > 0:
                warnings.append(
                    f"Instrument {instrument_id} is held but has no approved target."
                )

        if total_value == 0:
            warnings.append("Portfolio market value is zero.")

        weighted_fee = sum(
            (
                position.current_weight
                * instrument_by_id[position.instrument_id].annual_fee_rate
                for position in positions
            ),
            Decimal("0"),
        )
        maximum_weight = max(
            (position.current_weight for position in positions),
            default=Decimal("0"),
        )
        herfindahl = sum(
            (position.current_weight * position.current_weight for position in positions),
            Decimal("0"),
        )
        concentrated = tuple(
            position.instrument_id
            for position in positions
            if position.current_weight > _CONCENTRATION_THRESHOLD
        )

    return AnalysisResult(
        id=f"analysis:{state.investor_profile.id}:{valuation_date}",
        calculation_version=CALCULATION_VERSION,
        valuation_date=valuation_date,
        base_currency=state.investor_profile.base_currency,
        total_value=total_value,
        positions=tuple(positions),
        weighted_annual_fee_rate=weighted_fee,
        maximum_direct_weight=maximum_weight,
        herfindahl_index=herfindahl,
        concentrated_instrument_ids=concentrated,
        source_ids=tuple(sorted(used_sources)),
        warnings=tuple(warnings),
    )


def _fee(value: Decimal, constraint: TradingConstraint) -> Decimal:
    if value <= 0:
        return Decimal("0")
    raw_fee = constraint.fixed_fee + value * constraint.variable_fee_rate
    return max(constraint.minimum_fee, raw_fee).quantize(
        _CENT, rounding=ROUND_CEILING
    )


def _floor_to_increment(value: Decimal, increment: Decimal) -> Decimal:
    if value <= 0:
        return Decimal("0")
    units = (value / increment).to_integral_value(rounding=ROUND_FLOOR)
    return units * increment


def _execute_budget(
    budget: Decimal,
    price: Decimal,
    increment: Decimal,
    constraint: TradingConstraint,
) -> tuple[Decimal, Decimal, Decimal]:
    """Return quantity, purchase value, and fee without exceeding one budget."""

    if budget <= 0:
        return Decimal("0"), Decimal("0"), Decimal("0")
    fee_limited = budget - constraint.minimum_fee
    variable_limited = (
        (budget - constraint.fixed_fee) / (Decimal("1") + constraint.variable_fee_rate)
    )
    maximum_value = min(fee_limited, variable_limited)
    if maximum_value <= 0:
        return Decimal("0"), Decimal("0"), Decimal("0")

    quantity = _floor_to_increment(maximum_value / price, increment)
    for _ in range(8):
        if quantity <= 0:
            return Decimal("0"), Decimal("0"), Decimal("0")
        purchase_value = quantity * price
        trade_fee = _fee(purchase_value, constraint)
        excess = purchase_value + trade_fee - budget
        if excess <= 0:
            if purchase_value < constraint.minimum_trade_value:
                return Decimal("0"), Decimal("0"), Decimal("0")
            return quantity, purchase_value, trade_fee
        steps = max(
            Decimal("1"),
            (excess / (price * increment)).to_integral_value(
                rounding=ROUND_CEILING
            ),
        )
        quantity -= steps * increment
    raise ValidationError("Trade rounding did not converge within its budget.")


def _listing_for_instrument(
    instrument_id: str,
    listings: Sequence[Listing],
    preferred_listings: Mapping[str, str],
) -> Listing:
    candidates = [
        listing for listing in listings if listing.instrument_id == instrument_id
    ]
    preferred_id = preferred_listings.get(instrument_id)
    if preferred_id is not None:
        for listing in candidates:
            if listing.id == preferred_id:
                return listing
        raise ValidationError("A preferred listing does not match its instrument.")
    if len(candidates) != 1:
        raise ValidationError(
            "Each target instrument needs exactly one listing or an explicit preference."
        )
    return candidates[0]


def _validate_constraint(constraint: TradingConstraint) -> None:
    values = (
        constraint.minimum_trade_value,
        constraint.fixed_fee,
        constraint.variable_fee_rate,
        constraint.minimum_fee,
    )
    if any(value < 0 or not value.is_finite() for value in values):
        raise ValidationError("Trading constraints must be finite and non-negative.")
    if constraint.quantity_increment is not None and (
        constraint.quantity_increment <= 0
        or not constraint.quantity_increment.is_finite()
    ):
        raise ValidationError("A quantity increment must be positive and finite.")


def plan_contribution(
    state: PortfolioState,
    analysis: AnalysisResult,
    prices: Sequence[MarketPrice],
    fx_rates: Sequence[FxRate],
    contribution_amount: Decimal,
    currency: str,
    method: str,
    valuation_date: str,
    constraints: Sequence[TradingConstraint] = (),
    preferred_listings: Mapping[str, str] | None = None,
) -> ContributionPlan:
    """Create a buy-only contribution proposal without mutating source records."""

    validate_state(state)
    if method not in {"simple", "drift_aware"}:
        raise ValidationError("Contribution method must be simple or drift_aware.")
    if contribution_amount <= 0 or not contribution_amount.is_finite():
        raise ValidationError("Contribution amount must be positive and finite.")
    if currency != state.investor_profile.base_currency:
        raise ValidationError("MVP contributions must use the portfolio base currency.")
    if analysis.base_currency != currency or analysis.valuation_date != valuation_date:
        raise ValidationError("Analysis currency and date must match the contribution.")
    expected_analysis = analyze_portfolio(state, prices, fx_rates, valuation_date)
    if analysis != expected_analysis:
        raise ValidationError("Analysis does not match the supplied state and market inputs.")

    approved = _approved_target(state)
    target_weights = {
        target.instrument_id: target.weight for target in approved.targets
    }
    analysis_by_id = {
        position.instrument_id: position for position in analysis.positions
    }
    preferred = preferred_listings or {}
    constraint_by_listing: dict[str, TradingConstraint] = {}
    listing_ids = {listing.id for listing in state.listings}
    for constraint in constraints:
        _validate_constraint(constraint)
        if constraint.listing_id not in listing_ids:
            raise ValidationError("A trading constraint references an unknown listing.")
        if constraint.listing_id in constraint_by_listing:
            raise ValidationError("Only one constraint is allowed per listing.")
        constraint_by_listing[constraint.listing_id] = constraint

    selected_prices = _latest_prices(state, prices, valuation_date)
    fx_table = _FxTable(state, fx_rates, valuation_date)

    with localcontext() as context:
        context.prec = 36
        if method == "simple":
            budgets = {
                instrument_id: contribution_amount * weight
                for instrument_id, weight in target_weights.items()
            }
        else:
            future_value = analysis.total_value + contribution_amount
            deficits = {
                instrument_id: max(
                    Decimal("0"),
                    weight * future_value
                    - analysis_by_id[instrument_id].current_value,
                )
                for instrument_id, weight in target_weights.items()
            }
            total_deficit = sum(deficits.values(), Decimal("0"))
            basis = deficits if total_deficit > 0 else target_weights
            basis_total = sum(basis.values(), Decimal("0"))
            budgets = {
                instrument_id: contribution_amount * value / basis_total
                for instrument_id, value in basis.items()
            }

        provisional: list[
            tuple[
                str,
                str,
                Decimal,
                Decimal,
                Decimal,
                Decimal,
                Decimal,
                Decimal,
            ]
        ] = []
        used_sources = set(analysis.source_ids)
        warnings: list[str] = []
        for target in approved.targets:
            instrument_id = target.instrument_id
            listing = _listing_for_instrument(
                instrument_id, state.listings, preferred
            )
            price = selected_prices.get(listing.id)
            if price is None:
                raise MissingPriceError(
                    f"No dated market price for target listing {listing.id!r}."
                )
            base_price, fx_source = fx_table.convert(
                price.amount,
                listing.trading_currency,
                state.investor_profile.base_currency,
            )
            used_sources.add(price.source_id)
            if fx_source is not None:
                used_sources.add(fx_source)

            constraint = constraint_by_listing.get(
                listing.id, TradingConstraint(listing_id=listing.id)
            )
            fractional = (
                listing.fractional_allowed
                if constraint.fractional_allowed is None
                else constraint.fractional_allowed
            )
            increment = (
                constraint.quantity_increment
                if constraint.quantity_increment is not None
                else listing.quantity_increment
            )
            if not fractional:
                increment = Decimal("1")
            quantity, purchase_value, trade_fee = _execute_budget(
                budgets[instrument_id], base_price, increment, constraint
            )
            if quantity == 0 and budgets[instrument_id] > 0:
                warnings.append(
                    f"No executable buy for {instrument_id} within its budget and constraints."
                )
            position = analysis_by_id[instrument_id]
            provisional.append(
                (
                    instrument_id,
                    listing.id,
                    position.current_weight,
                    target.weight,
                    position.drift,
                    quantity,
                    purchase_value,
                    trade_fee,
                )
            )

        total_purchase = sum((line[6] for line in provisional), Decimal("0"))
        total_fees = sum((line[7] for line in provisional), Decimal("0"))
        remaining_cash = contribution_amount - total_purchase - total_fees
        if remaining_cash < 0:
            raise ValidationError("Contribution plan overspent available cash.")
        post_value = analysis.total_value + contribution_amount - total_fees
        if post_value <= 0:
            raise ValidationError("Expected post-contribution value must be positive.")

        lines: list[ContributionLine] = []
        for provisional_line in provisional:
            (
                instrument_id,
                listing_id,
                current_weight,
                target_weight,
                drift,
                quantity,
                purchase_value,
                trade_fee,
            ) = provisional_line
            post_instrument_value = (
                analysis_by_id[instrument_id].current_value + purchase_value
            )
            post_weight = post_instrument_value / post_value
            lines.append(
                ContributionLine(
                    instrument_id=instrument_id,
                    listing_id=listing_id,
                    current_weight=current_weight,
                    target_weight=target_weight,
                    drift=drift,
                    quantity=quantity,
                    proposed_contribution=purchase_value,
                    estimated_trade_cost=trade_fee,
                    expected_post_contribution_weight=post_weight,
                    remaining_drift=post_weight - target_weight,
                )
            )

        reconciled = total_purchase + total_fees + remaining_cash
        if reconciled != contribution_amount:
            raise ValidationError("Contribution plan does not conserve available cash.")

    return ContributionPlan(
        id=f"contribution:{state.investor_profile.id}:{valuation_date}:{method}",
        calculation_version=CALCULATION_VERSION,
        method=method,
        valuation_date=valuation_date,
        contribution_amount=contribution_amount,
        currency=currency,
        lines=tuple(lines),
        total_purchase_value=total_purchase,
        total_estimated_trade_cost=total_fees,
        remaining_cash=remaining_cash,
        expected_post_contribution_value=post_value,
        source_ids=tuple(sorted(used_sources)),
        warnings=tuple(warnings),
    )
