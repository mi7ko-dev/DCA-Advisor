"""Configurable, non-mutating checks over an analyzed invested portfolio."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import re
from typing import Any

from .errors import ValidationError
from .models import AnalysisResult, PortfolioState
from .validation import validate_analysis_result, validate_state


PORTFOLIO_POLICY_VERSION = "1.0"
PORTFOLIO_POLICY_CALCULATION_VERSION = "1.0"
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_DECIMAL = re.compile(r"^(0|[1-9][0-9]*)(\.[0-9]+)?$")


@dataclass(frozen=True)
class FactorGroupPolicy:
    id: str
    instrument_ids: tuple[str, ...]
    previous_reported_weight: Decimal | None = None
    change_alert_threshold: Decimal = Decimal("0.05")


@dataclass(frozen=True)
class PortfolioPolicy:
    id: str
    version: str
    analysis_base: str
    max_direct_weight: Decimal
    direct_weight_exempt_instrument_ids: tuple[str, ...]
    fragmentation_weight_threshold: Decimal
    max_fragmented_positions: int
    satellite_instrument_ids: tuple[str, ...]
    max_satellite_weight: Decimal
    factor_groups: tuple[FactorGroupPolicy, ...] = ()


@dataclass(frozen=True)
class FactorGroupAssessment:
    id: str
    current_weight: Decimal
    previous_reported_weight: Decimal | None
    change: Decimal | None
    change_alert: bool
    instrument_ids: tuple[str, ...]


@dataclass(frozen=True)
class PortfolioPolicyResult:
    id: str
    calculation_version: str
    policy_id: str
    policy_version: str
    analysis_id: str
    analysis_base: str
    direct_weight_breaches: tuple[str, ...]
    fragmented_instrument_ids: tuple[str, ...]
    fragmentation_limit_breached: bool
    satellite_weight: Decimal
    satellite_limit_breached: bool
    factor_groups: tuple[FactorGroupAssessment, ...]
    warnings: tuple[str, ...]
    mutation_performed: bool


def _parse_decimal(value: Any, field: str) -> Decimal:
    if not isinstance(value, str) or not _DECIMAL.fullmatch(value):
        raise ValidationError(f"{field} must be a canonical non-negative decimal string.")
    try:
        parsed = Decimal(value)
    except InvalidOperation as error:
        raise ValidationError(f"{field} must be a decimal string.") from error
    if not parsed.is_finite():
        raise ValidationError(f"{field} must be finite.")
    return parsed


def _parse_ids(value: Any, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValidationError(f"{field} must be an array of identifiers.")
    return tuple(value)


def portfolio_policy_from_dict(value: Any) -> PortfolioPolicy:
    """Parse an explicit policy instance intended for ignored private storage."""

    if not isinstance(value, dict):
        raise ValidationError("portfolio_policy must be an object.")
    allowed = {
        "id",
        "version",
        "analysis_base",
        "max_direct_weight",
        "direct_weight_exempt_instrument_ids",
        "fragmentation_weight_threshold",
        "max_fragmented_positions",
        "satellite_instrument_ids",
        "max_satellite_weight",
        "factor_groups",
    }
    if set(value) - allowed:
        raise ValidationError("portfolio_policy contains unsupported fields.")
    factor_raw = value.get("factor_groups", [])
    if not isinstance(factor_raw, list):
        raise ValidationError("factor_groups must be an array.")
    groups: list[FactorGroupPolicy] = []
    for raw in factor_raw:
        if not isinstance(raw, dict):
            raise ValidationError("factor_groups[] must be an object.")
        if set(raw) - {
            "id",
            "instrument_ids",
            "previous_reported_weight",
            "change_alert_threshold",
        }:
            raise ValidationError("factor_groups[] contains unsupported fields.")
        previous = raw.get("previous_reported_weight")
        groups.append(
            FactorGroupPolicy(
                id=raw.get("id") if isinstance(raw.get("id"), str) else "",
                instrument_ids=_parse_ids(
                    raw.get("instrument_ids"), "factor_groups[].instrument_ids"
                ),
                previous_reported_weight=(
                    _parse_decimal(previous, "factor_groups[].previous_reported_weight")
                    if previous is not None
                    else None
                ),
                change_alert_threshold=_parse_decimal(
                    raw.get("change_alert_threshold", "0.05"),
                    "factor_groups[].change_alert_threshold",
                ),
            )
        )
    maximum_fragments = value.get("max_fragmented_positions")
    if not isinstance(maximum_fragments, int) or isinstance(maximum_fragments, bool):
        raise ValidationError("max_fragmented_positions must be an integer.")
    for field in ("id", "version", "analysis_base"):
        if not isinstance(value.get(field), str) or not value[field]:
            raise ValidationError(f"{field} must be a non-empty string.")
    return PortfolioPolicy(
        id=value["id"],
        version=value["version"],
        analysis_base=value["analysis_base"],
        max_direct_weight=_parse_decimal(
            value.get("max_direct_weight"), "max_direct_weight"
        ),
        direct_weight_exempt_instrument_ids=_parse_ids(
            value.get("direct_weight_exempt_instrument_ids"),
            "direct_weight_exempt_instrument_ids",
        ),
        fragmentation_weight_threshold=_parse_decimal(
            value.get("fragmentation_weight_threshold"),
            "fragmentation_weight_threshold",
        ),
        max_fragmented_positions=maximum_fragments,
        satellite_instrument_ids=_parse_ids(
            value.get("satellite_instrument_ids"), "satellite_instrument_ids"
        ),
        max_satellite_weight=_parse_decimal(
            value.get("max_satellite_weight"), "max_satellite_weight"
        ),
        factor_groups=tuple(groups),
    )


def _weight(value: Decimal, field: str) -> None:
    if not value.is_finite() or not Decimal("0") <= value <= Decimal("1"):
        raise ValidationError(f"{field} must be between zero and one.")


def _unique_known_ids(
    values: tuple[str, ...],
    known: set[str],
    field: str,
) -> None:
    if len(set(values)) != len(values):
        raise ValidationError(f"{field} must contain unique instrument identifiers.")
    if not set(values) <= known:
        raise ValidationError(f"{field} references an unknown instrument.")


def evaluate_portfolio_policy(
    state: PortfolioState,
    analysis: AnalysisResult,
    policy: PortfolioPolicy,
) -> PortfolioPolicyResult:
    """Evaluate explicit user policy without changing state or inventing cash."""

    validate_state(state)
    validate_analysis_result(analysis)
    if policy.version != PORTFOLIO_POLICY_VERSION:
        raise ValidationError("Unsupported portfolio policy version.")
    if not _IDENTIFIER.fullmatch(policy.id):
        raise ValidationError("Portfolio policy id is invalid.")
    if policy.analysis_base != "invested_positions":
        raise ValidationError("Only the explicit invested_positions analysis base is supported.")
    _weight(policy.max_direct_weight, "max_direct_weight")
    _weight(
        policy.fragmentation_weight_threshold,
        "fragmentation_weight_threshold",
    )
    _weight(policy.max_satellite_weight, "max_satellite_weight")
    if policy.max_fragmented_positions < 0:
        raise ValidationError("max_fragmented_positions cannot be negative.")

    known = {instrument.id for instrument in state.instruments}
    _unique_known_ids(
        policy.direct_weight_exempt_instrument_ids,
        known,
        "direct_weight_exempt_instrument_ids",
    )
    _unique_known_ids(
        policy.satellite_instrument_ids,
        known,
        "satellite_instrument_ids",
    )
    position_ids = {position.instrument_id for position in analysis.positions}
    approved = next(
        allocation
        for allocation in state.target_allocations
        if allocation.status == "approved"
    )
    listing_instruments = {
        listing.id: listing.instrument_id for listing in state.listings
    }
    expected_position_ids = {
        target.instrument_id for target in approved.targets
    } | {
        listing_instruments[holding.listing_id]
        for holding in state.holdings
        if holding.quantity > 0
    }
    if position_ids != expected_position_ids:
        raise ValidationError(
            "Portfolio analysis coverage must match current holdings and approved targets."
        )
    if analysis.base_currency != state.investor_profile.base_currency:
        raise ValidationError("Portfolio analysis base currency differs from portfolio state.")

    group_ids: set[str] = set()
    for group in policy.factor_groups:
        if not _IDENTIFIER.fullmatch(group.id) or group.id in group_ids:
            raise ValidationError("Factor group identifiers must be valid and unique.")
        group_ids.add(group.id)
        if not group.instrument_ids:
            raise ValidationError("A factor group must contain at least one instrument.")
        _unique_known_ids(group.instrument_ids, known, "factor_groups[].instrument_ids")
        _weight(group.change_alert_threshold, "factor_groups[].change_alert_threshold")
        if group.previous_reported_weight is not None:
            _weight(
                group.previous_reported_weight,
                "factor_groups[].previous_reported_weight",
            )

    weights = {
        position.instrument_id: position.current_weight
        for position in analysis.positions
    }
    exempt = set(policy.direct_weight_exempt_instrument_ids)
    direct_breaches = tuple(
        sorted(
            instrument_id
            for instrument_id, weight in weights.items()
            if weight > policy.max_direct_weight and instrument_id not in exempt
        )
    )
    fragmented = tuple(
        sorted(
            instrument_id
            for instrument_id, weight in weights.items()
            if Decimal("0") < weight < policy.fragmentation_weight_threshold
        )
    )
    satellite_weight = sum(
        (
            weights.get(instrument_id, Decimal("0"))
            for instrument_id in policy.satellite_instrument_ids
        ),
        Decimal("0"),
    )

    group_results: list[FactorGroupAssessment] = []
    for group in policy.factor_groups:
        current = sum(
            (weights.get(instrument_id, Decimal("0")) for instrument_id in group.instrument_ids),
            Decimal("0"),
        )
        change = (
            current - group.previous_reported_weight
            if group.previous_reported_weight is not None
            else None
        )
        group_results.append(
            FactorGroupAssessment(
                id=group.id,
                current_weight=current,
                previous_reported_weight=group.previous_reported_weight,
                change=change,
                change_alert=(
                    change is not None
                    and abs(change) > group.change_alert_threshold
                ),
                instrument_ids=group.instrument_ids,
            )
        )

    return PortfolioPolicyResult(
        id=f"policy-check:{policy.id}:{analysis.valuation_date}",
        calculation_version=PORTFOLIO_POLICY_CALCULATION_VERSION,
        policy_id=policy.id,
        policy_version=policy.version,
        analysis_id=analysis.id,
        analysis_base=policy.analysis_base,
        direct_weight_breaches=direct_breaches,
        fragmented_instrument_ids=fragmented,
        fragmentation_limit_breached=(
            len(fragmented) > policy.max_fragmented_positions
        ),
        satellite_weight=satellite_weight,
        satellite_limit_breached=satellite_weight > policy.max_satellite_weight,
        factor_groups=tuple(group_results),
        warnings=(
            "Weights use invested positions only; unmodelled cash is excluded "
            "from the denominator.",
        ),
        mutation_performed=False,
    )


def validate_portfolio_policy_result(result: PortfolioPolicyResult) -> None:
    """Reject inconsistent constructed policy results before persistence."""

    if result.calculation_version != PORTFOLIO_POLICY_CALCULATION_VERSION:
        raise ValidationError("Unsupported portfolio-policy calculation version.")
    if result.policy_version != PORTFOLIO_POLICY_VERSION:
        raise ValidationError("Unsupported portfolio policy version in result.")
    if result.analysis_base != "invested_positions" or result.mutation_performed:
        raise ValidationError("Portfolio-policy result boundary is invalid.")
    _weight(result.satellite_weight, "satellite_weight")
    for values, field in (
        (result.direct_weight_breaches, "direct_weight_breaches"),
        (result.fragmented_instrument_ids, "fragmented_instrument_ids"),
    ):
        if len(set(values)) != len(values):
            raise ValidationError(f"{field} must contain unique identifiers.")
    group_ids: set[str] = set()
    for group in result.factor_groups:
        if not _IDENTIFIER.fullmatch(group.id) or group.id in group_ids:
            raise ValidationError("Policy-result factor groups must be valid and unique.")
        group_ids.add(group.id)
        _weight(group.current_weight, "factor_groups[].current_weight")
        if group.previous_reported_weight is not None:
            _weight(
                group.previous_reported_weight,
                "factor_groups[].previous_reported_weight",
            )
            if group.change != group.current_weight - group.previous_reported_weight:
                raise ValidationError("Policy-result factor-group change is inconsistent.")
        elif group.change is not None:
            raise ValidationError("A factor-group change requires a previous weight.")
