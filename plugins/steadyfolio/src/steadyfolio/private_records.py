"""Validated append-only records for private research and durable context."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
import re
from typing import Any, Mapping, Sequence
from uuid import uuid4

from .errors import ValidationError


PRIVATE_RECORD_SCHEMA_VERSION = "1.0"
CONTEXT_CATEGORIES = frozenset(
    {
        "confirmed_fact",
        "user_decision",
        "temporary_assumption",
        "proposal",
        "external_evidence",
    }
)
RESEARCH_CACHE_MODES = frozenset({"derived_summary", "citation_metadata"})
NON_AUTHORITATIVE_CONTEXT_STATUSES = {
    "temporary_assumption": frozenset({"pending", "expired", "rejected", "withdrawn"}),
    "proposal": frozenset({"pending", "rejected", "withdrawn"}),
}

_RECORD_ID = re.compile(r"^(research|context):[0-9a-f]{32}$")
_CURRENCY = re.compile(r"^[A-Z]{3}$")


@dataclass(frozen=True)
class ResearchCacheRecord:
    schema_version: str
    record_id: str
    asset_identity: str
    ticker: str | None
    currency: str
    data_kind: str
    conclusion: str
    facts: tuple[str, ...]
    source_title: str
    publisher: str
    source_reference: str
    primary_source: bool
    source_as_of: str | None
    source_period: str | None
    retrieved_at: str
    methodology: str
    coverage: str
    limitations: tuple[str, ...]
    assumptions: tuple[str, ...]
    freshness_basis: str
    refresh_after: str | None
    material_event_trigger: str | None
    terms_reference: str
    cache_mode: str
    redistribution_permitted: bool


@dataclass(frozen=True)
class DurableContextRecord:
    schema_version: str
    record_id: str
    category: str
    statement: str
    recorded_at: str
    effective_as_of: str | None
    source_kind: str
    source_reference: str | None
    status: str
    limitations: tuple[str, ...]
    review_after: str | None
    supersedes_record_id: str | None


def _require_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{field} must be a string.")
    if "\x00" in value:
        raise ValidationError(f"{field} cannot contain null bytes.")
    return value


def _require_string(value: object, field: str) -> str:
    parsed = _require_text(value, field)
    if not parsed.strip():
        raise ValidationError(f"{field} must be a non-empty string.")
    return parsed


def _optional_string(value: object, field: str) -> str | None:
    if value is None:
        return None
    return _require_string(value, field)


def _require_bool(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValidationError(f"{field} must be boolean.")
    return value


def _string_tuple(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValidationError(f"{field} must be an array.")
    parsed = tuple(_require_string(item, f"{field}[]") for item in value)
    if len(set(parsed)) != len(parsed):
        raise ValidationError(f"{field} must not contain duplicates.")
    return parsed


def _mapping(value: object, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValidationError(f"{field} must be an object.")
    return value


def _exact_keys(
    value: Mapping[str, Any],
    *,
    required: set[str],
    optional: set[str],
    field: str,
) -> None:
    keys = set(value)
    if not required <= keys or not keys <= required | optional:
        raise ValidationError(f"{field} has missing or unknown fields.")


def _require_iso_date(value: str | None, field: str) -> None:
    if value is None:
        return
    try:
        date.fromisoformat(value)
    except ValueError as error:
        raise ValidationError(f"{field} must be an ISO date.") from error


def _require_aware_datetime(value: str | None, field: str) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValidationError(f"{field} must be an ISO date-time.") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValidationError(f"{field} must include a timezone offset.")
    return parsed


def _record_id(prefix: str) -> str:
    return f"{prefix}:{uuid4().hex}"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def create_research_cache_record(
    *,
    asset_identity: str,
    ticker: str | None,
    currency: str,
    data_kind: str,
    conclusion: str,
    facts: Sequence[str],
    source_title: str,
    publisher: str,
    source_reference: str,
    primary_source: bool,
    source_as_of: str | None,
    source_period: str | None,
    retrieved_at: str,
    methodology: str,
    coverage: str,
    limitations: Sequence[str],
    assumptions: Sequence[str],
    freshness_basis: str,
    refresh_after: str | None,
    material_event_trigger: str | None,
    terms_reference: str,
    cache_mode: str,
    redistribution_permitted: bool,
) -> ResearchCacheRecord:
    """Create a validated cache record with a collision-resistant public id."""

    record = ResearchCacheRecord(
        schema_version=PRIVATE_RECORD_SCHEMA_VERSION,
        record_id=_record_id("research"),
        asset_identity=asset_identity,
        ticker=ticker,
        currency=currency,
        data_kind=data_kind,
        conclusion=conclusion,
        facts=tuple(facts),
        source_title=source_title,
        publisher=publisher,
        source_reference=source_reference,
        primary_source=primary_source,
        source_as_of=source_as_of,
        source_period=source_period,
        retrieved_at=retrieved_at,
        methodology=methodology,
        coverage=coverage,
        limitations=tuple(limitations),
        assumptions=tuple(assumptions),
        freshness_basis=freshness_basis,
        refresh_after=refresh_after,
        material_event_trigger=material_event_trigger,
        terms_reference=terms_reference,
        cache_mode=cache_mode,
        redistribution_permitted=redistribution_permitted,
    )
    validate_research_cache_record(record)
    return record


def validate_research_cache_record(record: ResearchCacheRecord) -> None:
    if record.schema_version != PRIVATE_RECORD_SCHEMA_VERSION:
        raise ValidationError("Unsupported research cache record version.")
    if not _RECORD_ID.fullmatch(record.record_id) or not record.record_id.startswith(
        "research:"
    ):
        raise ValidationError("Research cache record_id is invalid.")
    for field, value in (
        ("asset_identity", record.asset_identity),
        ("data_kind", record.data_kind),
        ("source_title", record.source_title),
        ("publisher", record.publisher),
        ("source_reference", record.source_reference),
        ("methodology", record.methodology),
        ("coverage", record.coverage),
        ("freshness_basis", record.freshness_basis),
        ("terms_reference", record.terms_reference),
    ):
        _require_string(value, field)
    _optional_string(record.ticker, "ticker")
    if not _CURRENCY.fullmatch(record.currency):
        raise ValidationError("currency must be an uppercase ISO 4217 code.")
    _require_bool(record.primary_source, "primary_source")
    _require_bool(record.redistribution_permitted, "redistribution_permitted")
    _require_iso_date(record.source_as_of, "source_as_of")
    _optional_string(record.source_period, "source_period")
    if record.source_as_of is None and record.source_period is None:
        raise ValidationError("Research records require source_as_of or source_period.")
    _require_aware_datetime(record.retrieved_at, "retrieved_at")
    _require_aware_datetime(record.refresh_after, "refresh_after")
    _optional_string(record.material_event_trigger, "material_event_trigger")
    _string_tuple(record.facts, "facts")
    _string_tuple(record.limitations, "limitations")
    _string_tuple(record.assumptions, "assumptions")
    if record.cache_mode not in RESEARCH_CACHE_MODES:
        raise ValidationError("Research cache_mode is unsupported.")
    if record.cache_mode == "derived_summary":
        _require_string(record.conclusion, "conclusion")
    elif record.conclusion != "" or record.facts:
        raise ValidationError(
            "Citation-metadata-only records cannot retain a conclusion or facts."
        )


def research_cache_record_from_dict(value: object) -> ResearchCacheRecord:
    raw = _mapping(value, "research_cache_record")
    required = {
        "schema_version",
        "record_id",
        "asset_identity",
        "currency",
        "data_kind",
        "conclusion",
        "facts",
        "source_title",
        "publisher",
        "source_reference",
        "primary_source",
        "retrieved_at",
        "methodology",
        "coverage",
        "limitations",
        "assumptions",
        "freshness_basis",
        "terms_reference",
        "cache_mode",
        "redistribution_permitted",
    }
    optional = {
        "ticker",
        "source_as_of",
        "source_period",
        "refresh_after",
        "material_event_trigger",
    }
    _exact_keys(raw, required=required, optional=optional, field="research_cache_record")
    record = ResearchCacheRecord(
        schema_version=_require_string(raw["schema_version"], "schema_version"),
        record_id=_require_string(raw["record_id"], "record_id"),
        asset_identity=_require_string(raw["asset_identity"], "asset_identity"),
        ticker=_optional_string(raw.get("ticker"), "ticker"),
        currency=_require_string(raw["currency"], "currency"),
        data_kind=_require_string(raw["data_kind"], "data_kind"),
        conclusion=_require_text(raw["conclusion"], "conclusion"),
        facts=_string_tuple(raw["facts"], "facts"),
        source_title=_require_string(raw["source_title"], "source_title"),
        publisher=_require_string(raw["publisher"], "publisher"),
        source_reference=_require_string(raw["source_reference"], "source_reference"),
        primary_source=_require_bool(raw["primary_source"], "primary_source"),
        source_as_of=_optional_string(raw.get("source_as_of"), "source_as_of"),
        source_period=_optional_string(raw.get("source_period"), "source_period"),
        retrieved_at=_require_string(raw["retrieved_at"], "retrieved_at"),
        methodology=_require_string(raw["methodology"], "methodology"),
        coverage=_require_string(raw["coverage"], "coverage"),
        limitations=_string_tuple(raw["limitations"], "limitations"),
        assumptions=_string_tuple(raw["assumptions"], "assumptions"),
        freshness_basis=_require_string(raw["freshness_basis"], "freshness_basis"),
        refresh_after=_optional_string(raw.get("refresh_after"), "refresh_after"),
        material_event_trigger=_optional_string(
            raw.get("material_event_trigger"), "material_event_trigger"
        ),
        terms_reference=_require_string(raw["terms_reference"], "terms_reference"),
        cache_mode=_require_string(raw["cache_mode"], "cache_mode"),
        redistribution_permitted=_require_bool(
            raw["redistribution_permitted"], "redistribution_permitted"
        ),
    )
    validate_research_cache_record(record)
    return record


def create_durable_context_record(
    *,
    category: str,
    statement: str,
    source_kind: str,
    status: str,
    limitations: Sequence[str] = (),
    recorded_at: str | None = None,
    effective_as_of: str | None = None,
    source_reference: str | None = None,
    review_after: str | None = None,
    supersedes_record_id: str | None = None,
) -> DurableContextRecord:
    """Create a classified immutable context record with a unique public id."""

    record = DurableContextRecord(
        schema_version=PRIVATE_RECORD_SCHEMA_VERSION,
        record_id=_record_id("context"),
        category=category,
        statement=statement,
        recorded_at=recorded_at or _utc_now(),
        effective_as_of=effective_as_of,
        source_kind=source_kind,
        source_reference=source_reference,
        status=status,
        limitations=tuple(limitations),
        review_after=review_after,
        supersedes_record_id=supersedes_record_id,
    )
    validate_durable_context_record(record)
    return record


def validate_durable_context_record(record: DurableContextRecord) -> None:
    if record.schema_version != PRIVATE_RECORD_SCHEMA_VERSION:
        raise ValidationError("Unsupported durable context record version.")
    if not _RECORD_ID.fullmatch(record.record_id) or not record.record_id.startswith(
        "context:"
    ):
        raise ValidationError("Durable context record_id is invalid.")
    if record.category not in CONTEXT_CATEGORIES:
        raise ValidationError("Durable context category is unsupported.")
    for field, value in (
        ("statement", record.statement),
        ("source_kind", record.source_kind),
        ("status", record.status),
    ):
        _require_string(value, field)
    allowed_statuses = NON_AUTHORITATIVE_CONTEXT_STATUSES.get(record.category)
    if allowed_statuses is not None and record.status not in allowed_statuses:
        raise ValidationError(
            f"{record.category} status cannot represent approved or active policy."
        )
    _require_aware_datetime(record.recorded_at, "recorded_at")
    _require_iso_date(record.effective_as_of, "effective_as_of")
    _require_iso_date(record.review_after, "review_after")
    _optional_string(record.source_reference, "source_reference")
    _string_tuple(record.limitations, "limitations")
    if record.supersedes_record_id is not None:
        if not _RECORD_ID.fullmatch(record.supersedes_record_id) or not record.supersedes_record_id.startswith(
            "context:"
        ):
            raise ValidationError("supersedes_record_id is invalid.")
        if record.supersedes_record_id == record.record_id:
            raise ValidationError("A context record cannot supersede itself.")


def durable_context_record_from_dict(value: object) -> DurableContextRecord:
    raw = _mapping(value, "durable_context_record")
    required = {
        "schema_version",
        "record_id",
        "category",
        "statement",
        "recorded_at",
        "source_kind",
        "status",
        "limitations",
    }
    optional = {
        "effective_as_of",
        "source_reference",
        "review_after",
        "supersedes_record_id",
    }
    _exact_keys(raw, required=required, optional=optional, field="durable_context_record")
    record = DurableContextRecord(
        schema_version=_require_string(raw["schema_version"], "schema_version"),
        record_id=_require_string(raw["record_id"], "record_id"),
        category=_require_string(raw["category"], "category"),
        statement=_require_string(raw["statement"], "statement"),
        recorded_at=_require_string(raw["recorded_at"], "recorded_at"),
        effective_as_of=_optional_string(raw.get("effective_as_of"), "effective_as_of"),
        source_kind=_require_string(raw["source_kind"], "source_kind"),
        source_reference=_optional_string(raw.get("source_reference"), "source_reference"),
        status=_require_string(raw["status"], "status"),
        limitations=_string_tuple(raw["limitations"], "limitations"),
        review_after=_optional_string(raw.get("review_after"), "review_after"),
        supersedes_record_id=_optional_string(
            raw.get("supersedes_record_id"), "supersedes_record_id"
        ),
    )
    validate_durable_context_record(record)
    return record
