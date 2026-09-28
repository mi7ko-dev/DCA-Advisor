"""Strict parsing for public equity-review evidence contracts."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
import re
from typing import Any

from .equity_models import (
    BooleanEvidence,
    CircleOfCompetenceEvidence,
    DecimalEvidence,
    EquityQualityEvidence,
    EquityReviewInput,
    FreeCashFlowObservation,
    InstrumentIdentityEvidence,
    OwnerEarningsEvidence,
    ValuationAnchor,
)
from .errors import ValidationError
from .research_models import ResearchSource


_DECIMAL = re.compile(r"^-?(0|[1-9][0-9]*)(\.[0-9]+)?$")


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{field} must be an object.")
    return value


def _sequence(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValidationError(f"{field} must be an array.")
    return value


def _string(value: Any, field: str, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field} must be a non-empty string.")
    return value


def _boolean(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValidationError(f"{field} must be a boolean.")
    return value


def _integer(value: Any, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValidationError(f"{field} must be an integer.")
    return value


def _decimal(value: Any, field: str) -> Decimal:
    if not isinstance(value, str) or not _DECIMAL.fullmatch(value):
        raise ValidationError(f"{field} must be a canonical decimal string.")
    try:
        parsed = Decimal(value)
    except InvalidOperation as error:
        raise ValidationError(f"{field} must be a decimal string.") from error
    if not parsed.is_finite():
        raise ValidationError(f"{field} must be finite.")
    return parsed


def _only(raw: dict[str, Any], allowed: set[str], field: str) -> None:
    unexpected = set(raw) - allowed
    if unexpected:
        raise ValidationError(f"{field} contains unsupported fields.")


def _decimal_evidence(value: Any, field: str) -> DecimalEvidence | None:
    if value is None:
        return None
    raw = _mapping(value, field)
    _only(raw, {"value", "as_of", "source_id"}, field)
    return DecimalEvidence(
        value=_decimal(raw.get("value"), f"{field}.value"),
        as_of=_string(raw.get("as_of"), f"{field}.as_of") or "",
        source_id=_string(raw.get("source_id"), f"{field}.source_id") or "",
    )


def _boolean_evidence(value: Any, field: str) -> BooleanEvidence | None:
    if value is None:
        return None
    raw = _mapping(value, field)
    _only(raw, {"value", "rationale", "as_of", "source_id"}, field)
    return BooleanEvidence(
        value=_boolean(raw.get("value"), f"{field}.value"),
        rationale=_string(raw.get("rationale"), f"{field}.rationale") or "",
        as_of=_string(raw.get("as_of"), f"{field}.as_of") or "",
        source_id=_string(raw.get("source_id"), f"{field}.source_id") or "",
    )


def _source(value: Any, field: str) -> ResearchSource:
    raw = _mapping(value, field)
    allowed = {
        "id",
        "provider",
        "reference",
        "as_of",
        "retrieved_at",
        "methodology",
        "limitations",
        "freshness_days",
        "terms_reference",
        "cache_permitted",
        "redistribution_permitted",
    }
    _only(raw, allowed, field)
    limitations = tuple(
        _string(item, f"{field}.limitations[]") or ""
        for item in _sequence(raw.get("limitations"), f"{field}.limitations")
    )
    return ResearchSource(
        id=_string(raw.get("id"), f"{field}.id") or "",
        provider=_string(raw.get("provider"), f"{field}.provider") or "",
        reference=_string(raw.get("reference"), f"{field}.reference") or "",
        as_of=_string(raw.get("as_of"), f"{field}.as_of") or "",
        retrieved_at=_string(raw.get("retrieved_at"), f"{field}.retrieved_at") or "",
        methodology=_string(raw.get("methodology"), f"{field}.methodology") or "",
        limitations=limitations,
        freshness_days=_integer(raw.get("freshness_days"), f"{field}.freshness_days"),
        terms_reference=_string(raw.get("terms_reference"), f"{field}.terms_reference") or "",
        cache_permitted=_boolean(raw.get("cache_permitted"), f"{field}.cache_permitted"),
        redistribution_permitted=_boolean(
            raw.get("redistribution_permitted"),
            f"{field}.redistribution_permitted",
        ),
    )


def equity_review_input_from_dict(value: Any) -> EquityReviewInput:
    """Parse strict JSON-compatible equity evidence without silent coercion."""

    raw = _mapping(value, "equity_review")
    _only(
        raw,
        {
            "schema_version",
            "as_of",
            "identity",
            "circle_of_competence",
            "quality",
            "valuation_anchors",
            "sources",
        },
        "equity_review",
    )
    identity_raw = _mapping(raw.get("identity"), "identity")
    _only(
        identity_raw,
        {
            "instrument_id",
            "reported_name",
            "isin",
            "source_id",
            "listing_id",
            "mic",
            "ticker",
            "trading_currency",
        },
        "identity",
    )
    identity = InstrumentIdentityEvidence(
        instrument_id=_string(identity_raw.get("instrument_id"), "identity.instrument_id") or "",
        reported_name=_string(identity_raw.get("reported_name"), "identity.reported_name") or "",
        isin=_string(identity_raw.get("isin"), "identity.isin") or "",
        source_id=_string(identity_raw.get("source_id"), "identity.source_id") or "",
        listing_id=_string(identity_raw.get("listing_id"), "identity.listing_id", optional=True),
        mic=_string(identity_raw.get("mic"), "identity.mic", optional=True),
        ticker=_string(identity_raw.get("ticker"), "identity.ticker", optional=True),
        trading_currency=_string(
            identity_raw.get("trading_currency"),
            "identity.trading_currency",
            optional=True,
        ),
    )

    circle_raw = _mapping(raw.get("circle_of_competence"), "circle_of_competence")
    _only(
        circle_raw,
        {
            "business_model_understood",
            "business_model_summary",
            "revenue_drivers_understood",
            "revenue_driver_summary",
            "external_dependency",
            "observable_event",
        },
        "circle_of_competence",
    )
    circle = CircleOfCompetenceEvidence(
        business_model_understood=_boolean(
            circle_raw.get("business_model_understood"),
            "circle_of_competence.business_model_understood",
        ),
        business_model_summary=_string(
            circle_raw.get("business_model_summary"),
            "circle_of_competence.business_model_summary",
        ) or "",
        revenue_drivers_understood=_boolean(
            circle_raw.get("revenue_drivers_understood"),
            "circle_of_competence.revenue_drivers_understood",
        ),
        revenue_driver_summary=_string(
            circle_raw.get("revenue_driver_summary"),
            "circle_of_competence.revenue_driver_summary",
        ) or "",
        external_dependency=_string(
            circle_raw.get("external_dependency"),
            "circle_of_competence.external_dependency",
            optional=True,
        ),
        observable_event=_string(
            circle_raw.get("observable_event"),
            "circle_of_competence.observable_event",
            optional=True,
        ),
    )

    quality_raw = _mapping(raw.get("quality"), "quality")
    _only(
        quality_raw,
        {
            "free_cash_flow",
            "debt_to_ebitda",
            "revenue_growth",
            "operating_margin",
            "capex_to_revenue",
            "institutional_ownership",
            "benchmark_outperformance",
            "moat_and_management",
            "owner_earnings",
        },
        "quality",
    )
    free_cash_flow_rows = tuple(
        _mapping(entry, "quality.free_cash_flow[]")
        for entry in _sequence(quality_raw.get("free_cash_flow"), "quality.free_cash_flow")
    )
    for item in free_cash_flow_rows:
        _only(
            item,
            {"period_end", "value", "source_id"},
            "quality.free_cash_flow[]",
        )
    free_cash_flow = tuple(
        FreeCashFlowObservation(
            period_end=_string(item.get("period_end"), "quality.free_cash_flow[].period_end") or "",
            value=_decimal(item.get("value"), "quality.free_cash_flow[].value"),
            source_id=_string(item.get("source_id"), "quality.free_cash_flow[].source_id") or "",
        )
        for item in free_cash_flow_rows
    )

    owner_raw_value = quality_raw.get("owner_earnings")
    owner = None
    if owner_raw_value is not None:
        owner_raw = _mapping(owner_raw_value, "quality.owner_earnings")
        _only(
            owner_raw,
            {
                "currency",
                "reported_earnings",
                "depreciation_and_amortization",
                "maintenance_capex",
                "growth_capex_funded_from_fcf",
            },
            "quality.owner_earnings",
        )
        owner = OwnerEarningsEvidence(
            currency=_string(owner_raw.get("currency"), "quality.owner_earnings.currency") or "",
            reported_earnings=_decimal_evidence(
                owner_raw.get("reported_earnings"),
                "quality.owner_earnings.reported_earnings",
            ),
            depreciation_and_amortization=_decimal_evidence(
                owner_raw.get("depreciation_and_amortization"),
                "quality.owner_earnings.depreciation_and_amortization",
            ),
            maintenance_capex=_decimal_evidence(
                owner_raw.get("maintenance_capex"),
                "quality.owner_earnings.maintenance_capex",
            ),
            growth_capex_funded_from_fcf=_boolean_evidence(
                owner_raw.get("growth_capex_funded_from_fcf"),
                "quality.owner_earnings.growth_capex_funded_from_fcf",
            ),
        )
    quality = EquityQualityEvidence(
        free_cash_flow=free_cash_flow,
        debt_to_ebitda=_decimal_evidence(
            quality_raw.get("debt_to_ebitda"), "quality.debt_to_ebitda"
        ),
        revenue_growth=_decimal_evidence(
            quality_raw.get("revenue_growth"), "quality.revenue_growth"
        ),
        operating_margin=_decimal_evidence(
            quality_raw.get("operating_margin"), "quality.operating_margin"
        ),
        capex_to_revenue=_decimal_evidence(
            quality_raw.get("capex_to_revenue"), "quality.capex_to_revenue"
        ),
        institutional_ownership=_decimal_evidence(
            quality_raw.get("institutional_ownership"),
            "quality.institutional_ownership",
        ),
        benchmark_outperformance=_boolean_evidence(
            quality_raw.get("benchmark_outperformance"),
            "quality.benchmark_outperformance",
        ),
        moat_and_management=_boolean_evidence(
            quality_raw.get("moat_and_management"),
            "quality.moat_and_management",
        ),
        owner_earnings=owner,
    )

    anchor_rows = tuple(
        _mapping(entry, "valuation_anchors[]")
        for entry in _sequence(raw.get("valuation_anchors"), "valuation_anchors")
    )
    for item in anchor_rows:
        _only(
            item,
            {
                "method",
                "current_price",
                "fair_value",
                "currency",
                "as_of",
                "source_ids",
                "rationale",
            },
            "valuation_anchors[]",
        )
    anchors = tuple(
        ValuationAnchor(
            method=_string(item.get("method"), "valuation_anchors[].method") or "",
            current_price=_decimal(item.get("current_price"), "valuation_anchors[].current_price"),
            fair_value=_decimal(item.get("fair_value"), "valuation_anchors[].fair_value"),
            currency=_string(item.get("currency"), "valuation_anchors[].currency") or "",
            as_of=_string(item.get("as_of"), "valuation_anchors[].as_of") or "",
            source_ids=tuple(
                _string(source_id, "valuation_anchors[].source_ids[]") or ""
                for source_id in _sequence(item.get("source_ids"), "valuation_anchors[].source_ids")
            ),
            rationale=_string(item.get("rationale"), "valuation_anchors[].rationale") or "",
        )
        for item in anchor_rows
    )
    sources = tuple(
        _source(entry, "sources[]")
        for entry in _sequence(raw.get("sources"), "sources")
    )
    return EquityReviewInput(
        schema_version=_string(raw.get("schema_version"), "schema_version") or "",
        as_of=_string(raw.get("as_of"), "as_of") or "",
        identity=identity,
        circle_of_competence=circle,
        quality=quality,
        valuation_anchors=anchors,
        sources=sources,
    )
