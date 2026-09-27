"""Parsing and domain validation for versioned JSON records."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import re
from typing import Any

from .errors import DuplicateIdentifierError, ValidationError
from .models import (
    SCHEMA_VERSION,
    Account,
    AllocationTarget,
    DataSource,
    FxRate,
    Goal,
    Holding,
    Instrument,
    InvestmentThesis,
    InvestorProfile,
    Listing,
    MarketPrice,
    PortfolioState,
    ReviewHistory,
    TargetAllocation,
    TradingConstraint,
    Transaction,
    to_json_value,
)


_CURRENCY = re.compile(r"^[A-Z]{3}$")
_MIC = re.compile(r"^[A-Z0-9]{4}$")
_ISIN = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_WEIGHT_TOLERANCE = Decimal("0.00000001")


def _require_fields(
    value: Mapping[str, Any],
    field: str,
    required: set[str],
    allowed: set[str],
) -> None:
    missing = required - set(value)
    unexpected = set(value) - allowed
    if missing:
        raise ValidationError(f"{field} is missing required fields: {sorted(missing)}.")
    if unexpected:
        raise ValidationError(f"{field} contains unknown fields: {sorted(unexpected)}.")


def _validate_document_shape(root: Mapping[str, Any]) -> None:
    collections: dict[str, tuple[set[str], set[str]]] = {
        "goals": (
            {"id", "name", "priority"},
            {"id", "name", "target_date", "target_amount", "currency", "priority"},
        ),
        "instruments": (
            {"id", "name", "kind", "economic_currency", "annual_fee_rate"},
            {"id", "name", "kind", "economic_currency", "isin", "annual_fee_rate"},
        ),
        "listings": (
            {
                "id",
                "instrument_id",
                "mic",
                "ticker",
                "trading_currency",
                "fractional_allowed",
                "quantity_increment",
            },
            {
                "id",
                "instrument_id",
                "mic",
                "ticker",
                "trading_currency",
                "fractional_allowed",
                "quantity_increment",
            },
        ),
        "accounts": (
            {"id", "name", "kind", "currency"},
            {"id", "name", "kind", "currency"},
        ),
        "holdings": (
            {"id", "account_id", "listing_id", "quantity"},
            {"id", "account_id", "listing_id", "quantity"},
        ),
        "transactions": (
            {
                "id",
                "account_id",
                "listing_id",
                "kind",
                "trade_date",
                "quantity",
                "unit_price",
                "price_currency",
                "fees",
            },
            {
                "id",
                "account_id",
                "listing_id",
                "kind",
                "trade_date",
                "quantity",
                "unit_price",
                "price_currency",
                "fees",
                "fee_currency",
            },
        ),
        "target_allocations": (
            {"id", "status", "effective_date", "targets", "rationale"},
            {"id", "status", "effective_date", "targets", "rationale"},
        ),
        "investment_theses": (
            {"id", "instrument_id", "status", "role", "rationale", "risks"},
            {
                "id",
                "instrument_id",
                "status",
                "role",
                "rationale",
                "risks",
                "review_date",
                "target_weight",
                "target_range_min",
                "target_range_max",
                "benchmark_instrument_id",
                "review_triggers",
                "last_review_date",
            },
        ),
        "data_sources": (
            {
                "id",
                "provider",
                "source_type",
                "value_time",
                "retrieved_at",
                "reference",
                "quality",
            },
            {
                "id",
                "provider",
                "source_type",
                "value_time",
                "retrieved_at",
                "reference",
                "quality",
            },
        ),
        "review_history": (
            {
                "id",
                "object_id",
                "reviewer_kind",
                "decision",
                "reviewed_at",
                "findings",
            },
            {
                "id",
                "object_id",
                "reviewer_kind",
                "decision",
                "reviewed_at",
                "findings",
            },
        ),
    }
    root_fields = {
        "schema_version",
        "investor_profile",
        *collections,
    }
    _require_fields(root, "portfolio", root_fields, root_fields)
    profile = _mapping(root["investor_profile"], "investor_profile")
    profile_fields = {"id", "base_currency", "jurisdiction", "goal_ids"}
    _require_fields(profile, "investor_profile", profile_fields, profile_fields)

    for collection, (required, allowed) in collections.items():
        for raw_item in _sequence(root[collection], collection):
            item = _mapping(raw_item, f"{collection}[]")
            _require_fields(item, f"{collection}[]", required, allowed)
            if collection == "target_allocations":
                for raw_target in _sequence(
                    item["targets"], "target_allocations[].targets"
                ):
                    target = _mapping(
                        raw_target, "target_allocations[].targets[]"
                    )
                    target_fields = {"instrument_id", "weight"}
                    _require_fields(
                        target,
                        "target_allocations[].targets[]",
                        target_fields,
                        target_fields,
                    )


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValidationError(f"{field} must be an object.")
    return value


def _sequence(value: Any, field: str) -> Sequence[Any]:
    if not isinstance(value, list):
        raise ValidationError(f"{field} must be an array.")
    return value


def _string(value: Any, field: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise ValidationError(f"{field} must be a non-empty string.")
    return value


def _optional_string(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return _string(value, field)


def _decimal(value: Any, field: str, *, optional: bool = False) -> Decimal | None:
    if value is None and optional:
        return None
    if not isinstance(value, str):
        raise ValidationError(f"{field} must be a decimal string.")
    try:
        parsed = Decimal(value)
    except InvalidOperation as error:
        raise ValidationError(f"{field} is not a valid decimal string.") from error
    if not parsed.is_finite():
        raise ValidationError(f"{field} must be finite.")
    return parsed


def _integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"{field} must be an integer.")
    return value


def _boolean(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValidationError(f"{field} must be a boolean.")
    return value


def _string_tuple(value: Any, field: str) -> tuple[str, ...]:
    return tuple(_string(item, f"{field}[]") for item in _sequence(value, field))


def _require_identifier(value: str, field: str) -> None:
    if not _IDENTIFIER.fullmatch(value):
        raise ValidationError(f"{field} is not a valid stable identifier.")


def _require_currency(value: str, field: str) -> None:
    if not _CURRENCY.fullmatch(value):
        raise ValidationError(f"{field} must be an uppercase ISO 4217 code.")


def _require_date(value: str, field: str) -> None:
    try:
        date.fromisoformat(value)
    except ValueError as error:
        raise ValidationError(f"{field} must be an ISO date.") from error


def _require_datetime(value: str, field: str) -> None:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValidationError(f"{field} must be an ISO date-time.") from error


def _ensure_unique(items: Iterable[Any], collection: str) -> dict[str, Any]:
    indexed: dict[str, Any] = {}
    for item in items:
        identifier = item.id
        if identifier in indexed:
            raise DuplicateIdentifierError(
                f"{collection} contains duplicate id {identifier!r}."
            )
        indexed[identifier] = item
    return indexed


def state_from_dict(raw: Mapping[str, Any]) -> PortfolioState:
    """Parse a JSON-compatible mapping and enforce the public decimal format."""

    root = _mapping(raw, "portfolio")
    _validate_document_shape(root)
    profile_raw = _mapping(root.get("investor_profile"), "investor_profile")
    profile = InvestorProfile(
        id=_string(profile_raw.get("id"), "investor_profile.id"),
        base_currency=_string(
            profile_raw.get("base_currency"), "investor_profile.base_currency"
        ),
        jurisdiction=_string(
            profile_raw.get("jurisdiction"), "investor_profile.jurisdiction"
        ),
        goal_ids=_string_tuple(
            profile_raw.get("goal_ids", []), "investor_profile.goal_ids"
        ),
    )

    goals = tuple(
        Goal(
            id=_string(item.get("id"), "goals[].id"),
            name=_string(item.get("name"), "goals[].name"),
            target_date=_optional_string(item.get("target_date"), "goals[].target_date"),
            target_amount=_decimal(
                item.get("target_amount"), "goals[].target_amount", optional=True
            ),
            currency=_optional_string(item.get("currency"), "goals[].currency"),
            priority=_integer(item.get("priority", 1), "goals[].priority"),
        )
        for item in (
            _mapping(value, "goals[]")
            for value in _sequence(root.get("goals", []), "goals")
        )
    )

    instruments = tuple(
        Instrument(
            id=_string(item.get("id"), "instruments[].id"),
            name=_string(item.get("name"), "instruments[].name"),
            kind=_string(item.get("kind"), "instruments[].kind"),
            economic_currency=_string(
                item.get("economic_currency"), "instruments[].economic_currency"
            ),
            isin=_optional_string(item.get("isin"), "instruments[].isin"),
            annual_fee_rate=_decimal(
                item.get("annual_fee_rate", "0"), "instruments[].annual_fee_rate"
            ),
        )
        for item in (
            _mapping(value, "instruments[]")
            for value in _sequence(root.get("instruments", []), "instruments")
        )
    )

    listings = tuple(
        Listing(
            id=_string(item.get("id"), "listings[].id"),
            instrument_id=_string(
                item.get("instrument_id"), "listings[].instrument_id"
            ),
            mic=_string(item.get("mic"), "listings[].mic"),
            ticker=_string(item.get("ticker"), "listings[].ticker"),
            trading_currency=_string(
                item.get("trading_currency"), "listings[].trading_currency"
            ),
            fractional_allowed=_boolean(
                item.get("fractional_allowed", True), "listings[].fractional_allowed"
            ),
            quantity_increment=_decimal(
                item.get("quantity_increment", "0.000001"),
                "listings[].quantity_increment",
            ),
        )
        for item in (
            _mapping(value, "listings[]")
            for value in _sequence(root.get("listings", []), "listings")
        )
    )

    accounts = tuple(
        Account(
            id=_string(item.get("id"), "accounts[].id"),
            name=_string(item.get("name"), "accounts[].name"),
            kind=_string(item.get("kind"), "accounts[].kind"),
            currency=_string(item.get("currency"), "accounts[].currency"),
        )
        for item in (
            _mapping(value, "accounts[]")
            for value in _sequence(root.get("accounts", []), "accounts")
        )
    )

    holdings = tuple(
        Holding(
            id=_string(item.get("id"), "holdings[].id"),
            account_id=_string(item.get("account_id"), "holdings[].account_id"),
            listing_id=_string(item.get("listing_id"), "holdings[].listing_id"),
            quantity=_decimal(item.get("quantity"), "holdings[].quantity"),
        )
        for item in (
            _mapping(value, "holdings[]")
            for value in _sequence(root.get("holdings", []), "holdings")
        )
    )

    transactions = tuple(
        Transaction(
            id=_string(item.get("id"), "transactions[].id"),
            account_id=_string(item.get("account_id"), "transactions[].account_id"),
            listing_id=_string(item.get("listing_id"), "transactions[].listing_id"),
            kind=_string(item.get("kind"), "transactions[].kind"),
            trade_date=_string(item.get("trade_date"), "transactions[].trade_date"),
            quantity=_decimal(item.get("quantity"), "transactions[].quantity"),
            unit_price=_decimal(item.get("unit_price"), "transactions[].unit_price"),
            price_currency=_string(
                item.get("price_currency"), "transactions[].price_currency"
            ),
            fees=_decimal(item.get("fees", "0"), "transactions[].fees"),
            fee_currency=_optional_string(
                item.get("fee_currency"), "transactions[].fee_currency"
            ),
        )
        for item in (
            _mapping(value, "transactions[]")
            for value in _sequence(root.get("transactions", []), "transactions")
        )
    )

    target_allocations = tuple(
        TargetAllocation(
            id=_string(item.get("id"), "target_allocations[].id"),
            status=_string(item.get("status"), "target_allocations[].status"),
            effective_date=_string(
                item.get("effective_date"), "target_allocations[].effective_date"
            ),
            targets=tuple(
                AllocationTarget(
                    instrument_id=_string(
                        target.get("instrument_id"),
                        "target_allocations[].targets[].instrument_id",
                    ),
                    weight=_decimal(
                        target.get("weight"),
                        "target_allocations[].targets[].weight",
                    ),
                )
                for target in (
                    _mapping(value, "target_allocations[].targets[]")
                    for value in _sequence(
                        item.get("targets", []), "target_allocations[].targets"
                    )
                )
            ),
            rationale=_string(
                item.get("rationale", ""),
                "target_allocations[].rationale",
                allow_empty=True,
            ),
        )
        for item in (
            _mapping(value, "target_allocations[]")
            for value in _sequence(
                root.get("target_allocations", []), "target_allocations"
            )
        )
    )

    investment_theses = tuple(
        InvestmentThesis(
            id=_string(item.get("id"), "investment_theses[].id"),
            instrument_id=_string(
                item.get("instrument_id"), "investment_theses[].instrument_id"
            ),
            status=_string(item.get("status"), "investment_theses[].status"),
            role=_string(item.get("role"), "investment_theses[].role"),
            rationale=_string(item.get("rationale"), "investment_theses[].rationale"),
            risks=_string_tuple(item.get("risks", []), "investment_theses[].risks"),
            review_date=_optional_string(
                item.get("review_date"), "investment_theses[].review_date"
            ),
            target_weight=_decimal(
                item.get("target_weight"),
                "investment_theses[].target_weight",
                optional=True,
            ),
            target_range_min=_decimal(
                item.get("target_range_min"),
                "investment_theses[].target_range_min",
                optional=True,
            ),
            target_range_max=_decimal(
                item.get("target_range_max"),
                "investment_theses[].target_range_max",
                optional=True,
            ),
            benchmark_instrument_id=_optional_string(
                item.get("benchmark_instrument_id"),
                "investment_theses[].benchmark_instrument_id",
            ),
            review_triggers=_string_tuple(
                item.get("review_triggers", []),
                "investment_theses[].review_triggers",
            ),
            last_review_date=_optional_string(
                item.get("last_review_date"),
                "investment_theses[].last_review_date",
            ),
        )
        for item in (
            _mapping(value, "investment_theses[]")
            for value in _sequence(
                root.get("investment_theses", []), "investment_theses"
            )
        )
    )

    data_sources = tuple(
        DataSource(
            id=_string(item.get("id"), "data_sources[].id"),
            provider=_string(item.get("provider"), "data_sources[].provider"),
            source_type=_string(
                item.get("source_type"), "data_sources[].source_type"
            ),
            value_time=_string(item.get("value_time"), "data_sources[].value_time"),
            retrieved_at=_string(
                item.get("retrieved_at"), "data_sources[].retrieved_at"
            ),
            reference=_string(item.get("reference"), "data_sources[].reference"),
            quality=_string(item.get("quality", "provided"), "data_sources[].quality"),
        )
        for item in (
            _mapping(value, "data_sources[]")
            for value in _sequence(root.get("data_sources", []), "data_sources")
        )
    )

    review_history = tuple(
        ReviewHistory(
            id=_string(item.get("id"), "review_history[].id"),
            object_id=_string(item.get("object_id"), "review_history[].object_id"),
            reviewer_kind=_string(
                item.get("reviewer_kind"), "review_history[].reviewer_kind"
            ),
            decision=_string(item.get("decision"), "review_history[].decision"),
            reviewed_at=_string(
                item.get("reviewed_at"), "review_history[].reviewed_at"
            ),
            findings=_string_tuple(
                item.get("findings", []), "review_history[].findings"
            ),
        )
        for item in (
            _mapping(value, "review_history[]")
            for value in _sequence(root.get("review_history", []), "review_history")
        )
    )

    state = PortfolioState(
        schema_version=_string(root.get("schema_version"), "schema_version"),
        investor_profile=profile,
        goals=goals,
        instruments=instruments,
        listings=listings,
        accounts=accounts,
        holdings=holdings,
        transactions=transactions,
        target_allocations=target_allocations,
        investment_theses=investment_theses,
        data_sources=data_sources,
        review_history=review_history,
    )
    validate_state(state)
    return state


def state_to_dict(state: PortfolioState) -> dict[str, Any]:
    validate_state(state)
    return to_json_value(state)


def market_prices_from_dict(raw: Sequence[Mapping[str, Any]]) -> tuple[MarketPrice, ...]:
    prices = tuple(
        MarketPrice(
            listing_id=_string(item.get("listing_id"), "prices[].listing_id"),
            amount=_decimal(item.get("amount"), "prices[].amount"),
            currency=_string(item.get("currency"), "prices[].currency"),
            as_of=_string(item.get("as_of"), "prices[].as_of"),
            source_id=_string(item.get("source_id"), "prices[].source_id"),
        )
        for item in (_mapping(value, "prices[]") for value in raw)
    )
    for price in prices:
        if price.amount <= 0:
            raise ValidationError("prices[].amount must be positive.")
        _require_currency(price.currency, "prices[].currency")
        _require_date(price.as_of, "prices[].as_of")
    return prices


def fx_rates_from_dict(raw: Sequence[Mapping[str, Any]]) -> tuple[FxRate, ...]:
    rates = tuple(
        FxRate(
            base_currency=_string(
                item.get("base_currency"), "fx_rates[].base_currency"
            ),
            quote_currency=_string(
                item.get("quote_currency"), "fx_rates[].quote_currency"
            ),
            rate=_decimal(item.get("rate"), "fx_rates[].rate"),
            as_of=_string(item.get("as_of"), "fx_rates[].as_of"),
            source_id=_string(item.get("source_id"), "fx_rates[].source_id"),
        )
        for item in (_mapping(value, "fx_rates[]") for value in raw)
    )
    for rate in rates:
        _require_currency(rate.base_currency, "fx_rates[].base_currency")
        _require_currency(rate.quote_currency, "fx_rates[].quote_currency")
        _require_date(rate.as_of, "fx_rates[].as_of")
        if rate.base_currency == rate.quote_currency or rate.rate <= 0:
            raise ValidationError("FX rates require two currencies and a positive rate.")
    return rates


def constraints_from_dict(
    raw: Sequence[Mapping[str, Any]],
) -> tuple[TradingConstraint, ...]:
    constraints = tuple(
        TradingConstraint(
            listing_id=_string(item.get("listing_id"), "constraints[].listing_id"),
            fractional_allowed=(
                None
                if item.get("fractional_allowed") is None
                else _boolean(
                    item.get("fractional_allowed"),
                    "constraints[].fractional_allowed",
                )
            ),
            quantity_increment=_decimal(
                item.get("quantity_increment"),
                "constraints[].quantity_increment",
                optional=True,
            ),
            minimum_trade_value=_decimal(
                item.get("minimum_trade_value", "0"),
                "constraints[].minimum_trade_value",
            ),
            fixed_fee=_decimal(item.get("fixed_fee", "0"), "constraints[].fixed_fee"),
            variable_fee_rate=_decimal(
                item.get("variable_fee_rate", "0"),
                "constraints[].variable_fee_rate",
            ),
            minimum_fee=_decimal(
                item.get("minimum_fee", "0"), "constraints[].minimum_fee"
            ),
        )
        for item in (_mapping(value, "constraints[]") for value in raw)
    )
    listing_ids: set[str] = set()
    for constraint in constraints:
        if constraint.listing_id in listing_ids:
            raise ValidationError("Only one constraint is allowed per listing.")
        listing_ids.add(constraint.listing_id)
        numeric = (
            constraint.minimum_trade_value,
            constraint.fixed_fee,
            constraint.variable_fee_rate,
            constraint.minimum_fee,
        )
        if any(value < 0 for value in numeric):
            raise ValidationError("Trading constraints cannot be negative.")
        if constraint.quantity_increment is not None and constraint.quantity_increment <= 0:
            raise ValidationError("A quantity increment must be positive.")
    return constraints


def validate_state(state: PortfolioState) -> None:
    """Validate references, identifiers, dates, currencies, and financial invariants."""

    if state.schema_version != SCHEMA_VERSION:
        raise ValidationError(f"Unsupported schema version {state.schema_version!r}.")

    _require_identifier(state.investor_profile.id, "investor_profile.id")
    _require_currency(
        state.investor_profile.base_currency, "investor_profile.base_currency"
    )
    if not state.investor_profile.jurisdiction.strip():
        raise ValidationError("investor_profile.jurisdiction cannot be empty.")

    collections = (
        (state.goals, "goals"),
        (state.instruments, "instruments"),
        (state.listings, "listings"),
        (state.accounts, "accounts"),
        (state.holdings, "holdings"),
        (state.transactions, "transactions"),
        (state.target_allocations, "target_allocations"),
        (state.investment_theses, "investment_theses"),
        (state.data_sources, "data_sources"),
        (state.review_history, "review_history"),
    )
    indexed = {
        name: _ensure_unique(items, name) for items, name in collections
    }
    goals = indexed["goals"]
    instruments = indexed["instruments"]
    listings = indexed["listings"]
    accounts = indexed["accounts"]
    for items, collection_name in collections:
        for item in items:
            _require_identifier(item.id, f"{collection_name}[].id")

    for goal_id in state.investor_profile.goal_ids:
        if goal_id not in goals:
            raise ValidationError("investor_profile.goal_ids references an unknown goal.")

    for goal in state.goals:
        if goal.priority < 1:
            raise ValidationError("Goal priority must be at least one.")
        if goal.target_date is not None:
            _require_date(goal.target_date, "goals[].target_date")
        if (goal.target_amount is None) != (goal.currency is None):
            raise ValidationError("Goal target amount and currency must appear together.")
        if goal.target_amount is not None and goal.target_amount < 0:
            raise ValidationError("Goal target amount cannot be negative.")
        if goal.currency is not None:
            _require_currency(goal.currency, "goals[].currency")

    for instrument in state.instruments:
        if instrument.kind not in {"etf", "stock"}:
            raise ValidationError("The MVP supports only ETF and stock instruments.")
        _require_currency(
            instrument.economic_currency, "instruments[].economic_currency"
        )
        if instrument.isin is not None and not _ISIN.fullmatch(instrument.isin):
            raise ValidationError("instruments[].isin is not a valid ISIN shape.")
        if not Decimal("0") <= instrument.annual_fee_rate <= Decimal("1"):
            raise ValidationError("Annual fee rates must be between zero and one.")

    listing_keys: set[tuple[str, str]] = set()
    for listing in state.listings:
        if listing.instrument_id not in instruments:
            raise ValidationError("A listing references an unknown instrument.")
        if not _MIC.fullmatch(listing.mic):
            raise ValidationError("listings[].mic must be a four-character MIC.")
        _require_currency(listing.trading_currency, "listings[].trading_currency")
        if listing.quantity_increment <= 0:
            raise ValidationError("Listing quantity increments must be positive.")
        key = (listing.mic, listing.ticker)
        if key in listing_keys:
            raise ValidationError("Duplicate MIC and ticker listing identity.")
        listing_keys.add(key)

    for account in state.accounts:
        _require_currency(account.currency, "accounts[].currency")

    for holding in state.holdings:
        if holding.account_id not in accounts or holding.listing_id not in listings:
            raise ValidationError("A holding references an unknown account or listing.")
        if holding.quantity < 0:
            raise ValidationError("Holding quantities cannot be negative.")

    for transaction in state.transactions:
        if transaction.account_id not in accounts or transaction.listing_id not in listings:
            raise ValidationError("A transaction references an unknown account or listing.")
        _require_date(transaction.trade_date, "transactions[].trade_date")
        _require_currency(transaction.price_currency, "transactions[].price_currency")
        if transaction.price_currency != listings[transaction.listing_id].trading_currency:
            raise ValidationError(
                "A transaction price currency differs from its listing currency."
            )
        if transaction.fee_currency is not None:
            _require_currency(transaction.fee_currency, "transactions[].fee_currency")
        if transaction.kind not in {"buy", "sell", "dividend", "fee", "transfer"}:
            raise ValidationError("Unknown transaction kind.")
        if transaction.quantity <= 0 or transaction.unit_price < 0 or transaction.fees < 0:
            raise ValidationError("Transaction quantity and monetary values are invalid.")

    approved_count = 0
    approved_target_weights: dict[str, Decimal] = {}
    for allocation in state.target_allocations:
        if allocation.status not in {"approved", "proposed", "superseded"}:
            raise ValidationError("Unknown target allocation status.")
        _require_date(allocation.effective_date, "target_allocations[].effective_date")
        target_ids: set[str] = set()
        total_weight = Decimal("0")
        for target in allocation.targets:
            if target.instrument_id not in instruments:
                raise ValidationError("A target references an unknown instrument.")
            if target.instrument_id in target_ids:
                raise ValidationError("An allocation repeats an instrument target.")
            if target.weight < 0 or target.weight > 1:
                raise ValidationError("Target weights must be between zero and one.")
            target_ids.add(target.instrument_id)
            total_weight += target.weight
        if abs(total_weight - Decimal("1")) > _WEIGHT_TOLERANCE:
            raise ValidationError("Target allocation weights must sum to one.")
        if allocation.status == "approved":
            approved_count += 1
            approved_target_weights = {
                target.instrument_id: target.weight for target in allocation.targets
            }
    if approved_count != 1:
        raise ValidationError("Exactly one approved target allocation is required.")

    active_thesis_instruments: set[str] = set()
    for thesis in state.investment_theses:
        if thesis.instrument_id not in instruments:
            raise ValidationError("An investment thesis references an unknown instrument.")
        if thesis.status not in {"active", "retired", "superseded"}:
            raise ValidationError("Unknown investment thesis status.")
        if thesis.status == "active":
            if thesis.instrument_id in active_thesis_instruments:
                raise ValidationError("Only one active thesis is allowed per instrument.")
            active_thesis_instruments.add(thesis.instrument_id)
        if thesis.review_date is not None:
            _require_date(thesis.review_date, "investment_theses[].review_date")
        if thesis.last_review_date is not None:
            _require_date(
                thesis.last_review_date, "investment_theses[].last_review_date"
            )
        if thesis.review_date is not None and thesis.last_review_date is not None:
            if date.fromisoformat(thesis.last_review_date) > date.fromisoformat(
                thesis.review_date
            ):
                raise ValidationError("A thesis last review cannot follow its next review.")
        weights = (
            thesis.target_weight,
            thesis.target_range_min,
            thesis.target_range_max,
        )
        if any(
            weight is not None
            and (not weight.is_finite() or weight < 0 or weight > 1)
            for weight in weights
        ):
            raise ValidationError("Thesis target weights must be between zero and one.")
        if (thesis.target_range_min is None) != (thesis.target_range_max is None):
            raise ValidationError("A thesis target range requires both bounds.")
        if (
            thesis.target_range_min is not None
            and thesis.target_range_max is not None
            and thesis.target_range_min > thesis.target_range_max
        ):
            raise ValidationError("A thesis target range is inverted.")
        if (
            thesis.target_weight is not None
            and thesis.target_range_min is not None
            and not (
                thesis.target_range_min
                <= thesis.target_weight
                <= thesis.target_range_max
            )
        ):
            raise ValidationError("A thesis target weight is outside its range.")
        approved_weight = approved_target_weights.get(thesis.instrument_id)
        if thesis.target_weight is not None and thesis.target_weight != approved_weight:
            raise ValidationError(
                "A thesis target weight must match the approved allocation."
            )
        if (
            thesis.benchmark_instrument_id is not None
            and thesis.benchmark_instrument_id not in instruments
        ):
            raise ValidationError("A thesis benchmark references an unknown instrument.")
        if len(set(thesis.review_triggers)) != len(thesis.review_triggers):
            raise ValidationError("Thesis review triggers must be unique.")

    for source in state.data_sources:
        _require_datetime(source.value_time, "data_sources[].value_time")
        _require_datetime(source.retrieved_at, "data_sources[].retrieved_at")

    for review in state.review_history:
        _require_datetime(review.reviewed_at, "review_history[].reviewed_at")
