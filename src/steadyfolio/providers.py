"""Replaceable provider boundary for structured portfolio research."""

from __future__ import annotations

from datetime import date
from typing import Protocol, runtime_checkable

from .errors import ValidationError
from .research_models import ResearchRequest, ResearchSnapshot
from .research_validation import validate_research_snapshot


@runtime_checkable
class ResearchProvider(Protocol):
    """Return structured data without receiving holdings, balances, or goals."""

    name: str

    def fetch(self, request: ResearchRequest) -> ResearchSnapshot:
        """Fetch data for explicit public instrument and listing identifiers."""


class StaticResearchProvider:
    """Offline provider for synthetic fixtures and deterministic tests."""

    def __init__(self, name: str, snapshot: ResearchSnapshot) -> None:
        if not name.strip():
            raise ValidationError("A provider name cannot be empty.")
        validate_research_snapshot(snapshot)
        self.name = name
        self._snapshot = snapshot

    def fetch(self, request: ResearchRequest) -> ResearchSnapshot:
        try:
            request_date = date.fromisoformat(request.as_of)
        except ValueError as error:
            raise ValidationError("Research request as_of must be an ISO date.") from error
        if len(set(request.instrument_ids)) != len(request.instrument_ids):
            raise ValidationError("Research request instrument identifiers must be unique.")
        if len(set(request.listing_ids)) != len(request.listing_ids):
            raise ValidationError("Research request listing identifiers must be unique.")
        if any(date.fromisoformat(source.as_of) > request_date for source in self._snapshot.sources):
            raise ValidationError("A provider snapshot cannot use data after the request date.")
        instrument_ids = set(request.instrument_ids)
        listing_ids = set(request.listing_ids)
        funds = tuple(
            item
            for item in self._snapshot.funds
            if item.instrument_id in instrument_ids
        )
        holdings = tuple(
            item
            for item in self._snapshot.fund_holdings
            if item.fund_instrument_id in instrument_ids
        )
        exposures = tuple(
            item
            for item in self._snapshot.classified_exposures
            if item.instrument_id in instrument_ids
        )
        series = tuple(
            item
            for item in self._snapshot.historical_series
            if item.listing_id in listing_ids
        )
        source_ids = {
            item.source_id for item in (*funds, *holdings, *exposures, *series)
        }
        return ResearchSnapshot(
            schema_version=self._snapshot.schema_version,
            sources=tuple(
                item for item in self._snapshot.sources if item.id in source_ids
            ),
            funds=funds,
            fund_holdings=holdings,
            classified_exposures=exposures,
            historical_series=series,
        )
