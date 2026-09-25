"""Strict parsing and validation for structured research inputs."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import re
from typing import Any

from .errors import ValidationError
from .research_models import (
    RESEARCH_SCHEMA_VERSION,
    ClassifiedExposure,
    FundHolding,
    FundProfile,
    HistoricalObservation,
    HistoricalSeries,
    ResearchSnapshot,
    ResearchSource,
    StressWindow,
    ThesisEvidence,
)


_CURRENCY = re.compile(r"^[A-Z]{3}$")
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_WEIGHT_TOLERANCE = Decimal("0.00000001")


def _object(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValidationError(f"{field} must be an object.")
    return value


def _array(value: Any, field: str) -> Sequence[Any]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValidationError(f"{field} must be an array.")
    return value


def _shape(
    value: Mapping[str, Any],
    field: str,
    required: set[str],
    optional: set[str] | None = None,
) -> None:
    optional = optional or set()
    missing = required - set(value)
    unexpected = set(value) - required - optional
    if missing:
        raise ValidationError(f"{field} is missing required fields: {sorted(missing)}.")
    if unexpected:
        raise ValidationError(f"{field} contains unknown fields: {sorted(unexpected)}.")


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field} must be a non-empty string.")
    return value


def _optional_string(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return _string(value, field)


def _strings(value: Any, field: str) -> tuple[str, ...]:
    return tuple(_string(item, f"{field}[]") for item in _array(value, field))


def _decimal(value: Any, field: str, *, optional: bool = False) -> Decimal | None:
    if value is None and optional:
        return None
    if not isinstance(value, str):
        raise ValidationError(f"{field} must be a decimal string.")
    try:
        result = Decimal(value)
    except InvalidOperation as error:
        raise ValidationError(f"{field} must be a decimal string.") from error
    if not result.is_finite():
        raise ValidationError(f"{field} must be finite.")
    return result


def _integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"{field} must be an integer.")
    return value


def _boolean(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValidationError(f"{field} must be a boolean.")
    return value


def _date(value: str, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValidationError(f"{field} must be an ISO date.") from error


def _datetime(value: str, field: str) -> datetime:
    try:
        result = datetime.fromisoformat(value)
    except ValueError as error:
        raise ValidationError(f"{field} must be an ISO datetime.") from error
    if result.tzinfo is None:
        raise ValidationError(f"{field} must include a timezone offset.")
    return result


def _identifier(value: str, field: str) -> None:
    if not _IDENTIFIER.fullmatch(value):
        raise ValidationError(f"{field} is not a stable identifier.")


def _currency(value: str, field: str) -> None:
    if not _CURRENCY.fullmatch(value):
        raise ValidationError(f"{field} must be an uppercase currency code.")


def research_snapshot_from_dict(raw: Mapping[str, Any]) -> ResearchSnapshot:
    """Parse a strict JSON-shaped research snapshot."""

    root = _object(raw, "research_snapshot")
    root_fields = {
        "schema_version",
        "sources",
        "funds",
        "fund_holdings",
        "classified_exposures",
        "historical_series",
    }
    _shape(root, "research_snapshot", root_fields)

    sources: list[ResearchSource] = []
    source_fields = {
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
    for raw_source in _array(root["sources"], "sources"):
        item = _object(raw_source, "sources[]")
        _shape(item, "sources[]", source_fields)
        sources.append(
            ResearchSource(
                id=_string(item["id"], "sources[].id"),
                provider=_string(item["provider"], "sources[].provider"),
                reference=_string(item["reference"], "sources[].reference"),
                as_of=_string(item["as_of"], "sources[].as_of"),
                retrieved_at=_string(item["retrieved_at"], "sources[].retrieved_at"),
                methodology=_string(item["methodology"], "sources[].methodology"),
                limitations=_strings(item["limitations"], "sources[].limitations"),
                freshness_days=_integer(
                    item["freshness_days"], "sources[].freshness_days"
                ),
                terms_reference=_string(
                    item["terms_reference"], "sources[].terms_reference"
                ),
                cache_permitted=_boolean(
                    item["cache_permitted"], "sources[].cache_permitted"
                ),
                redistribution_permitted=_boolean(
                    item["redistribution_permitted"],
                    "sources[].redistribution_permitted",
                ),
            )
        )

    funds: list[FundProfile] = []
    fund_required = {
        "instrument_id",
        "domicile",
        "distribution_policy",
        "as_of",
        "source_id",
    }
    fund_optional = {
        "index_name",
        "replication_method",
        "ter",
        "fund_size",
        "fund_size_currency",
    }
    for raw_fund in _array(root["funds"], "funds"):
        item = _object(raw_fund, "funds[]")
        _shape(item, "funds[]", fund_required, fund_optional)
        funds.append(
            FundProfile(
                instrument_id=_string(item["instrument_id"], "funds[].instrument_id"),
                domicile=_string(item["domicile"], "funds[].domicile"),
                distribution_policy=_string(
                    item["distribution_policy"], "funds[].distribution_policy"
                ),
                index_name=_optional_string(item.get("index_name"), "funds[].index_name"),
                replication_method=_optional_string(
                    item.get("replication_method"), "funds[].replication_method"
                ),
                ter=_decimal(item.get("ter"), "funds[].ter", optional=True),
                fund_size=_decimal(
                    item.get("fund_size"), "funds[].fund_size", optional=True
                ),
                fund_size_currency=_optional_string(
                    item.get("fund_size_currency"), "funds[].fund_size_currency"
                ),
                as_of=_string(item["as_of"], "funds[].as_of"),
                source_id=_string(item["source_id"], "funds[].source_id"),
            )
        )

    holdings: list[FundHolding] = []
    holding_fields = {
        "fund_instrument_id",
        "constituent_id",
        "constituent_name",
        "weight",
        "as_of",
        "source_id",
    }
    for raw_holding in _array(root["fund_holdings"], "fund_holdings"):
        item = _object(raw_holding, "fund_holdings[]")
        _shape(item, "fund_holdings[]", holding_fields)
        holdings.append(
            FundHolding(
                fund_instrument_id=_string(
                    item["fund_instrument_id"], "fund_holdings[].fund_instrument_id"
                ),
                constituent_id=_string(
                    item["constituent_id"], "fund_holdings[].constituent_id"
                ),
                constituent_name=_string(
                    item["constituent_name"], "fund_holdings[].constituent_name"
                ),
                weight=_decimal(item["weight"], "fund_holdings[].weight"),
                as_of=_string(item["as_of"], "fund_holdings[].as_of"),
                source_id=_string(item["source_id"], "fund_holdings[].source_id"),
            )
        )

    exposures: list[ClassifiedExposure] = []
    exposure_fields = {
        "instrument_id",
        "dimension",
        "label",
        "weight",
        "as_of",
        "source_id",
    }
    for raw_exposure in _array(
        root["classified_exposures"], "classified_exposures"
    ):
        item = _object(raw_exposure, "classified_exposures[]")
        _shape(item, "classified_exposures[]", exposure_fields)
        exposures.append(
            ClassifiedExposure(
                instrument_id=_string(
                    item["instrument_id"], "classified_exposures[].instrument_id"
                ),
                dimension=_string(
                    item["dimension"], "classified_exposures[].dimension"
                ),
                label=_string(item["label"], "classified_exposures[].label"),
                weight=_decimal(item["weight"], "classified_exposures[].weight"),
                as_of=_string(item["as_of"], "classified_exposures[].as_of"),
                source_id=_string(
                    item["source_id"], "classified_exposures[].source_id"
                ),
            )
        )

    series: list[HistoricalSeries] = []
    series_fields = {
        "listing_id",
        "currency",
        "frequency",
        "return_convention",
        "distribution_treatment",
        "corporate_action_treatment",
        "observations",
        "as_of",
        "source_id",
    }
    observation_fields = {"date", "value"}
    for raw_series in _array(root["historical_series"], "historical_series"):
        item = _object(raw_series, "historical_series[]")
        _shape(item, "historical_series[]", series_fields)
        observations: list[HistoricalObservation] = []
        for raw_observation in _array(
            item["observations"], "historical_series[].observations"
        ):
            observation = _object(
                raw_observation, "historical_series[].observations[]"
            )
            _shape(
                observation,
                "historical_series[].observations[]",
                observation_fields,
            )
            observations.append(
                HistoricalObservation(
                    date=_string(
                        observation["date"],
                        "historical_series[].observations[].date",
                    ),
                    value=_decimal(
                        observation["value"],
                        "historical_series[].observations[].value",
                    ),
                )
            )
        series.append(
            HistoricalSeries(
                listing_id=_string(item["listing_id"], "historical_series[].listing_id"),
                currency=_string(item["currency"], "historical_series[].currency"),
                frequency=_string(item["frequency"], "historical_series[].frequency"),
                return_convention=_string(
                    item["return_convention"], "historical_series[].return_convention"
                ),
                distribution_treatment=_string(
                    item["distribution_treatment"],
                    "historical_series[].distribution_treatment",
                ),
                corporate_action_treatment=_string(
                    item["corporate_action_treatment"],
                    "historical_series[].corporate_action_treatment",
                ),
                observations=tuple(observations),
                as_of=_string(item["as_of"], "historical_series[].as_of"),
                source_id=_string(item["source_id"], "historical_series[].source_id"),
            )
        )

    snapshot = ResearchSnapshot(
        schema_version=_string(root["schema_version"], "schema_version"),
        sources=tuple(sources),
        funds=tuple(funds),
        fund_holdings=tuple(holdings),
        classified_exposures=tuple(exposures),
        historical_series=tuple(series),
    )
    validate_research_snapshot(snapshot)
    return snapshot


def validate_research_snapshot(snapshot: ResearchSnapshot) -> None:
    if snapshot.schema_version != RESEARCH_SCHEMA_VERSION:
        raise ValidationError("Unsupported research snapshot schema version.")

    sources: dict[str, ResearchSource] = {}
    for source in snapshot.sources:
        _identifier(source.id, "sources[].id")
        if source.id in sources:
            raise ValidationError("Research source identifiers must be unique.")
        source_date = _date(source.as_of, "sources[].as_of")
        retrieved_at = _datetime(source.retrieved_at, "sources[].retrieved_at")
        if retrieved_at.date() < source_date:
            raise ValidationError("A research source cannot be retrieved before its as-of date.")
        if source.freshness_days < 0:
            raise ValidationError("Source freshness days cannot be negative.")
        sources[source.id] = source

    def validate_provenance(as_of: str, source_id: str, field: str) -> None:
        record_date = _date(as_of, f"{field}.as_of")
        source = sources.get(source_id)
        if source is None:
            raise ValidationError(f"{field} references an unknown research source.")
        if record_date > _date(source.as_of, "sources[].as_of"):
            raise ValidationError(f"{field} is newer than its research source.")

    fund_ids: set[str] = set()
    for fund in snapshot.funds:
        _identifier(fund.instrument_id, "funds[].instrument_id")
        if fund.instrument_id in fund_ids:
            raise ValidationError("Only one fund profile is allowed per instrument.")
        if fund.distribution_policy not in {"accumulating", "distributing", "unknown"}:
            raise ValidationError("Unknown fund distribution policy.")
        if fund.ter is not None and (
            not fund.ter.is_finite() or fund.ter < 0 or fund.ter > 1
        ):
            raise ValidationError("Fund TER must be between zero and one.")
        if fund.fund_size is not None and (
            not fund.fund_size.is_finite() or fund.fund_size < 0
        ):
            raise ValidationError("Fund size cannot be negative.")
        if (fund.fund_size is None) != (fund.fund_size_currency is None):
            raise ValidationError("Fund size and currency must be supplied together.")
        if fund.fund_size_currency is not None:
            _currency(fund.fund_size_currency, "funds[].fund_size_currency")
        validate_provenance(fund.as_of, fund.source_id, "funds[]")
        fund_ids.add(fund.instrument_id)

    holdings_by_fund: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    holding_keys: set[tuple[str, str]] = set()
    constituent_names: dict[str, str] = {}
    for holding in snapshot.fund_holdings:
        key = (holding.fund_instrument_id, holding.constituent_id)
        if key in holding_keys:
            raise ValidationError("A fund holding is duplicated.")
        _identifier(holding.fund_instrument_id, "fund_holdings[].fund_instrument_id")
        _identifier(holding.constituent_id, "fund_holdings[].constituent_id")
        if (
            not holding.weight.is_finite()
            or holding.weight < 0
            or holding.weight > 1
        ):
            raise ValidationError("Fund holding weights must be between zero and one.")
        previous_name = constituent_names.setdefault(
            holding.constituent_id, holding.constituent_name
        )
        if previous_name != holding.constituent_name:
            raise ValidationError("A constituent identifier has inconsistent names.")
        validate_provenance(holding.as_of, holding.source_id, "fund_holdings[]")
        holdings_by_fund[holding.fund_instrument_id] += holding.weight
        holding_keys.add(key)
    if any(total > Decimal("1") + _WEIGHT_TOLERANCE for total in holdings_by_fund.values()):
        raise ValidationError("Fund holding coverage cannot exceed one.")

    exposure_totals: dict[tuple[str, str], Decimal] = defaultdict(lambda: Decimal("0"))
    exposure_keys: set[tuple[str, str, str]] = set()
    for exposure in snapshot.classified_exposures:
        if exposure.dimension not in {"sector", "geography", "currency"}:
            raise ValidationError("Unknown classified exposure dimension.")
        key = (exposure.instrument_id, exposure.dimension, exposure.label)
        if key in exposure_keys:
            raise ValidationError("A classified exposure is duplicated.")
        if (
            not exposure.weight.is_finite()
            or exposure.weight < 0
            or exposure.weight > 1
        ):
            raise ValidationError("Classified exposure weights must be between zero and one.")
        validate_provenance(exposure.as_of, exposure.source_id, "classified_exposures[]")
        exposure_totals[(exposure.instrument_id, exposure.dimension)] += exposure.weight
        exposure_keys.add(key)
    if any(total > Decimal("1") + _WEIGHT_TOLERANCE for total in exposure_totals.values()):
        raise ValidationError("Classified exposure coverage cannot exceed one.")

    series_ids: set[str] = set()
    for series in snapshot.historical_series:
        if series.listing_id in series_ids:
            raise ValidationError("Only one historical series is allowed per listing.")
        _currency(series.currency, "historical_series[].currency")
        if series.frequency not in {"daily", "weekly", "monthly"}:
            raise ValidationError("Unknown historical series frequency.")
        if series.return_convention not in {"price_index", "total_return_index"}:
            raise ValidationError("Unknown historical return convention.")
        if series.distribution_treatment not in {"included", "excluded"}:
            raise ValidationError("Unknown distribution treatment.")
        if len(series.observations) < 2:
            raise ValidationError("Historical series need at least two observations.")
        dates = [_date(item.date, "historical_series[].observations[].date") for item in series.observations]
        if dates != sorted(dates) or len(set(dates)) != len(dates):
            raise ValidationError("Historical observation dates must be unique and increasing.")
        if any(item.value <= 0 or not item.value.is_finite() for item in series.observations):
            raise ValidationError("Historical index values must be positive and finite.")
        series_as_of = _date(series.as_of, "historical_series[].as_of")
        if dates[-1] > series_as_of:
            raise ValidationError("Historical observations cannot be newer than the series.")
        validate_provenance(series.as_of, series.source_id, "historical_series[]")
        series_ids.add(series.listing_id)


def stress_windows_from_dict(raw: Sequence[Mapping[str, Any]]) -> tuple[StressWindow, ...]:
    windows: list[StressWindow] = []
    fields = {"id", "name", "start_date", "end_date"}
    for raw_window in _array(raw, "stress_windows"):
        item = _object(raw_window, "stress_windows[]")
        _shape(item, "stress_windows[]", fields)
        window = StressWindow(
            id=_string(item["id"], "stress_windows[].id"),
            name=_string(item["name"], "stress_windows[].name"),
            start_date=_string(item["start_date"], "stress_windows[].start_date"),
            end_date=_string(item["end_date"], "stress_windows[].end_date"),
        )
        if _date(window.start_date, "stress_windows[].start_date") >= _date(
            window.end_date, "stress_windows[].end_date"
        ):
            raise ValidationError("A stress window must end after it starts.")
        windows.append(window)
    if len({window.id for window in windows}) != len(windows):
        raise ValidationError("Stress window identifiers must be unique.")
    return tuple(windows)


def thesis_evidence_from_dict(raw: Sequence[Mapping[str, Any]]) -> tuple[ThesisEvidence, ...]:
    evidence: list[ThesisEvidence] = []
    required = {
        "id",
        "instrument_id",
        "kind",
        "summary",
        "observed_at",
        "source_id",
        "assessment",
        "limitations",
    }
    for raw_item in _array(raw, "thesis_evidence"):
        item = _object(raw_item, "thesis_evidence[]")
        _shape(item, "thesis_evidence[]", required)
        parsed = ThesisEvidence(
            id=_string(item["id"], "thesis_evidence[].id"),
            instrument_id=_string(
                item["instrument_id"], "thesis_evidence[].instrument_id"
            ),
            kind=_string(item["kind"], "thesis_evidence[].kind"),
            summary=_string(item["summary"], "thesis_evidence[].summary"),
            observed_at=_string(
                item["observed_at"], "thesis_evidence[].observed_at"
            ),
            source_id=_string(item["source_id"], "thesis_evidence[].source_id"),
            assessment=_string(
                item["assessment"], "thesis_evidence[].assessment"
            ),
            limitations=_strings(
                item["limitations"], "thesis_evidence[].limitations"
            ),
        )
        _date(parsed.observed_at, "thesis_evidence[].observed_at")
        if parsed.assessment not in {"supports", "neutral", "contradicts"}:
            raise ValidationError("Unknown thesis evidence assessment.")
        evidence.append(parsed)
    if len({item.id for item in evidence}) != len(evidence):
        raise ValidationError("Thesis evidence identifiers must be unique.")
    return tuple(evidence)
