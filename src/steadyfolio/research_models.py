"""Immutable records for provider data and Phase 4 portfolio intelligence."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


RESEARCH_SCHEMA_VERSION = "1.0"
INTELLIGENCE_CALCULATION_VERSION = "1.0"


@dataclass(frozen=True)
class ResearchSource:
    id: str
    provider: str
    reference: str
    as_of: str
    retrieved_at: str
    methodology: str
    limitations: tuple[str, ...]
    freshness_days: int
    terms_reference: str
    cache_permitted: bool
    redistribution_permitted: bool


@dataclass(frozen=True)
class FundProfile:
    instrument_id: str
    domicile: str
    distribution_policy: str
    index_name: str | None
    replication_method: str | None
    ter: Decimal | None
    fund_size: Decimal | None
    fund_size_currency: str | None
    as_of: str
    source_id: str


@dataclass(frozen=True)
class FundHolding:
    fund_instrument_id: str
    constituent_id: str
    constituent_name: str
    weight: Decimal
    as_of: str
    source_id: str


@dataclass(frozen=True)
class ClassifiedExposure:
    instrument_id: str
    dimension: str
    label: str
    weight: Decimal
    as_of: str
    source_id: str


@dataclass(frozen=True)
class HistoricalObservation:
    date: str
    value: Decimal


@dataclass(frozen=True)
class HistoricalSeries:
    listing_id: str
    currency: str
    frequency: str
    return_convention: str
    distribution_treatment: str
    corporate_action_treatment: str
    observations: tuple[HistoricalObservation, ...]
    as_of: str
    source_id: str


@dataclass(frozen=True)
class ResearchSnapshot:
    schema_version: str
    sources: tuple[ResearchSource, ...]
    funds: tuple[FundProfile, ...]
    fund_holdings: tuple[FundHolding, ...]
    classified_exposures: tuple[ClassifiedExposure, ...]
    historical_series: tuple[HistoricalSeries, ...]


@dataclass(frozen=True)
class ResearchRequest:
    instrument_ids: tuple[str, ...]
    listing_ids: tuple[str, ...]
    as_of: str


@dataclass(frozen=True)
class StressWindow:
    id: str
    name: str
    start_date: str
    end_date: str


@dataclass(frozen=True)
class ThesisEvidence:
    id: str
    instrument_id: str
    kind: str
    summary: str
    observed_at: str
    source_id: str
    assessment: str
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True)
class SourceAssessment:
    source_id: str
    provider: str
    reference: str
    as_of: str
    retrieved_at: str
    age_days: int
    freshness: str
    methodology: str
    limitations: tuple[str, ...]
    terms_reference: str
    cache_permitted: bool
    redistribution_permitted: bool


@dataclass(frozen=True)
class ListingIdentity:
    listing_id: str
    mic: str
    ticker: str
    trading_currency: str


@dataclass(frozen=True)
class InstrumentResearchSummary:
    instrument_id: str
    name: str
    kind: str
    isin: str | None
    economic_currency: str
    listings: tuple[ListingIdentity, ...]
    domicile: str | None
    distribution_policy: str | None
    index_name: str | None
    replication_method: str | None
    ter: Decimal | None
    fund_size: Decimal | None
    fund_size_currency: str | None
    facts_as_of: str | None
    source_id: str | None
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class OverlapResult:
    left_instrument_id: str
    right_instrument_id: str
    observed_overlap_weight: Decimal
    left_holdings_coverage: Decimal
    right_holdings_coverage: Decimal
    holdings_as_of_dates: tuple[str, ...]
    source_ids: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class CompanyExposure:
    constituent_id: str
    name: str
    observed_portfolio_weight: Decimal


@dataclass(frozen=True)
class CompanyConcentration:
    exposures: tuple[CompanyExposure, ...]
    covered_portfolio_weight: Decimal
    unclassified_portfolio_weight: Decimal
    maximum_observed_company_weight: Decimal
    holdings_as_of_dates: tuple[str, ...]
    source_ids: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class ExposureEntry:
    label: str
    observed_portfolio_weight: Decimal


@dataclass(frozen=True)
class ExposureAnalysis:
    dimension: str
    entries: tuple[ExposureEntry, ...]
    covered_portfolio_weight: Decimal
    unclassified_portfolio_weight: Decimal
    as_of_dates: tuple[str, ...]
    source_ids: tuple[str, ...]
    methodologies: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class HistoricalMetric:
    instrument_id: str
    listing_id: str
    start_date: str
    end_date: str
    observation_count: int
    currency: str
    frequency: str
    return_convention: str
    distribution_treatment: str
    corporate_action_treatment: str
    cumulative_return: Decimal
    annualized_volatility: Decimal
    maximum_drawdown: Decimal
    benchmark_listing_id: str | None
    benchmark_cumulative_return: Decimal | None
    excess_return: Decimal | None
    source_ids: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class CorrelationMetric:
    left_instrument_id: str
    right_instrument_id: str
    start_date: str
    end_date: str
    return_observation_count: int
    correlation: Decimal
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class StressMetric:
    stress_id: str
    stress_name: str
    instrument_id: str
    listing_id: str
    start_date: str
    end_date: str
    observation_count: int
    cumulative_return: Decimal
    maximum_drawdown: Decimal
    source_id: str
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class PortfolioIntelligenceResult:
    id: str
    calculation_version: str
    analysis_date: str
    base_currency: str
    instrument_summaries: tuple[InstrumentResearchSummary, ...]
    overlaps: tuple[OverlapResult, ...]
    company_concentration: CompanyConcentration
    exposures: tuple[ExposureAnalysis, ...]
    historical_metrics: tuple[HistoricalMetric, ...]
    correlations: tuple[CorrelationMetric, ...]
    stress_metrics: tuple[StressMetric, ...]
    source_assessments: tuple[SourceAssessment, ...]
    source_ids: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class ThesisReviewResult:
    id: str
    calculation_version: str
    thesis_id: str
    instrument_id: str
    reviewed_at: str
    role: str
    rationale: str
    target_weight: Decimal | None
    target_range_min: Decimal | None
    target_range_max: Decimal | None
    benchmark_instrument_id: str | None
    risks: tuple[str, ...]
    last_review_date: str | None
    next_review_date: str | None
    configured_review_triggers: tuple[str, ...]
    evidence_facts: tuple[str, ...]
    interpretations: tuple[str, ...]
    triggered_review_conditions: tuple[str, ...]
    proposed_action: str
    proposed_changes: tuple[str, ...]
    source_assessments: tuple[SourceAssessment, ...]
    source_ids: tuple[str, ...]
    limitations: tuple[str, ...]
