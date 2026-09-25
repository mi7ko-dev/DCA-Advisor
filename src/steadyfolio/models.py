"""Immutable domain records for the SteadyFolio MVP."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal
from typing import Any


SCHEMA_VERSION = "1.0"
CALCULATION_VERSION = "1.0"


@dataclass(frozen=True)
class InvestorProfile:
    id: str
    base_currency: str
    jurisdiction: str
    goal_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class Goal:
    id: str
    name: str
    target_date: str | None = None
    target_amount: Decimal | None = None
    currency: str | None = None
    priority: int = 1


@dataclass(frozen=True)
class Instrument:
    id: str
    name: str
    kind: str
    economic_currency: str
    isin: str | None = None
    annual_fee_rate: Decimal = Decimal("0")


@dataclass(frozen=True)
class Listing:
    id: str
    instrument_id: str
    mic: str
    ticker: str
    trading_currency: str
    fractional_allowed: bool = True
    quantity_increment: Decimal = Decimal("0.000001")


@dataclass(frozen=True)
class Account:
    id: str
    name: str
    kind: str
    currency: str


@dataclass(frozen=True)
class Holding:
    id: str
    account_id: str
    listing_id: str
    quantity: Decimal


@dataclass(frozen=True)
class Transaction:
    id: str
    account_id: str
    listing_id: str
    kind: str
    trade_date: str
    quantity: Decimal
    unit_price: Decimal
    price_currency: str
    fees: Decimal = Decimal("0")
    fee_currency: str | None = None


@dataclass(frozen=True)
class AllocationTarget:
    instrument_id: str
    weight: Decimal


@dataclass(frozen=True)
class TargetAllocation:
    id: str
    status: str
    effective_date: str
    targets: tuple[AllocationTarget, ...]
    rationale: str = ""


@dataclass(frozen=True)
class InvestmentThesis:
    id: str
    instrument_id: str
    status: str
    role: str
    rationale: str
    risks: tuple[str, ...] = ()
    review_date: str | None = None


@dataclass(frozen=True)
class DataSource:
    id: str
    provider: str
    source_type: str
    value_time: str
    retrieved_at: str
    reference: str
    quality: str = "provided"


@dataclass(frozen=True)
class ReviewHistory:
    id: str
    object_id: str
    reviewer_kind: str
    decision: str
    reviewed_at: str
    findings: tuple[str, ...] = ()


@dataclass(frozen=True)
class PortfolioState:
    schema_version: str
    investor_profile: InvestorProfile
    goals: tuple[Goal, ...] = ()
    instruments: tuple[Instrument, ...] = ()
    listings: tuple[Listing, ...] = ()
    accounts: tuple[Account, ...] = ()
    holdings: tuple[Holding, ...] = ()
    transactions: tuple[Transaction, ...] = ()
    target_allocations: tuple[TargetAllocation, ...] = ()
    investment_theses: tuple[InvestmentThesis, ...] = ()
    data_sources: tuple[DataSource, ...] = ()
    review_history: tuple[ReviewHistory, ...] = ()


@dataclass(frozen=True)
class MarketPrice:
    listing_id: str
    amount: Decimal
    currency: str
    as_of: str
    source_id: str


@dataclass(frozen=True)
class FxRate:
    base_currency: str
    quote_currency: str
    rate: Decimal
    as_of: str
    source_id: str


@dataclass(frozen=True)
class TradingConstraint:
    listing_id: str
    fractional_allowed: bool | None = None
    quantity_increment: Decimal | None = None
    minimum_trade_value: Decimal = Decimal("0")
    fixed_fee: Decimal = Decimal("0")
    variable_fee_rate: Decimal = Decimal("0")
    minimum_fee: Decimal = Decimal("0")


@dataclass(frozen=True)
class PositionAnalysis:
    instrument_id: str
    current_value: Decimal
    current_weight: Decimal
    target_weight: Decimal
    drift: Decimal


@dataclass(frozen=True)
class AnalysisResult:
    id: str
    calculation_version: str
    valuation_date: str
    base_currency: str
    total_value: Decimal
    positions: tuple[PositionAnalysis, ...]
    weighted_annual_fee_rate: Decimal
    maximum_direct_weight: Decimal
    herfindahl_index: Decimal
    concentrated_instrument_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class ContributionLine:
    instrument_id: str
    listing_id: str
    current_weight: Decimal
    target_weight: Decimal
    drift: Decimal
    quantity: Decimal
    proposed_contribution: Decimal
    estimated_trade_cost: Decimal
    expected_post_contribution_weight: Decimal
    remaining_drift: Decimal


@dataclass(frozen=True)
class ContributionPlan:
    id: str
    calculation_version: str
    method: str
    valuation_date: str
    contribution_amount: Decimal
    currency: str
    lines: tuple[ContributionLine, ...]
    total_purchase_value: Decimal
    total_estimated_trade_cost: Decimal
    remaining_cash: Decimal
    expected_post_contribution_value: Decimal
    source_ids: tuple[str, ...]
    warnings: tuple[str, ...] = ()


def decimal_to_string(value: Decimal) -> str:
    """Return a non-exponent decimal representation suitable for JSON."""

    rendered = format(value, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered or "0"


def to_json_value(value: Any) -> Any:
    """Convert immutable domain records to JSON-compatible primitives."""

    if isinstance(value, Decimal):
        return decimal_to_string(value)
    if is_dataclass(value):
        return {
            field.name: to_json_value(item)
            for field in fields(value)
            if (item := getattr(value, field.name)) is not None
        }
    if isinstance(value, tuple):
        return [to_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): to_json_value(item) for key, item in value.items()}
    return value
