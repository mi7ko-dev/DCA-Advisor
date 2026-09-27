"""Immutable records for evidence-limited individual-equity review."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .research_models import ResearchSource, SourceAssessment


EQUITY_EVIDENCE_SCHEMA_VERSION = "1.0"
EQUITY_REVIEW_VERSION = "1.0"
EQUITY_QUALITY_MODEL = "equity_quality_v1"


@dataclass(frozen=True)
class DecimalEvidence:
    value: Decimal
    as_of: str
    source_id: str


@dataclass(frozen=True)
class BooleanEvidence:
    value: bool
    rationale: str
    as_of: str
    source_id: str


@dataclass(frozen=True)
class FreeCashFlowObservation:
    period_end: str
    value: Decimal
    source_id: str


@dataclass(frozen=True)
class InstrumentIdentityEvidence:
    instrument_id: str
    reported_name: str
    isin: str
    source_id: str
    listing_id: str | None = None
    mic: str | None = None
    ticker: str | None = None
    trading_currency: str | None = None


@dataclass(frozen=True)
class CircleOfCompetenceEvidence:
    business_model_understood: bool
    business_model_summary: str
    revenue_drivers_understood: bool
    revenue_driver_summary: str
    external_dependency: str | None
    observable_event: str | None


@dataclass(frozen=True)
class OwnerEarningsEvidence:
    currency: str
    reported_earnings: DecimalEvidence | None = None
    depreciation_and_amortization: DecimalEvidence | None = None
    maintenance_capex: DecimalEvidence | None = None
    growth_capex_funded_from_fcf: BooleanEvidence | None = None


@dataclass(frozen=True)
class EquityQualityEvidence:
    free_cash_flow: tuple[FreeCashFlowObservation, ...]
    debt_to_ebitda: DecimalEvidence | None = None
    revenue_growth: DecimalEvidence | None = None
    operating_margin: DecimalEvidence | None = None
    capex_to_revenue: DecimalEvidence | None = None
    institutional_ownership: DecimalEvidence | None = None
    benchmark_outperformance: BooleanEvidence | None = None
    moat_and_management: BooleanEvidence | None = None
    owner_earnings: OwnerEarningsEvidence | None = None


@dataclass(frozen=True)
class ValuationAnchor:
    method: str
    current_price: Decimal
    fair_value: Decimal
    currency: str
    as_of: str
    source_ids: tuple[str, ...]
    rationale: str


@dataclass(frozen=True)
class EquityReviewInput:
    schema_version: str
    as_of: str
    identity: InstrumentIdentityEvidence
    circle_of_competence: CircleOfCompetenceEvidence
    quality: EquityQualityEvidence
    valuation_anchors: tuple[ValuationAnchor, ...]
    sources: tuple[ResearchSource, ...]


@dataclass(frozen=True)
class CriterionAssessment:
    criterion: str
    status: str
    points_awarded: Decimal
    maximum_points: Decimal
    observed_value: str | None
    rationale: str
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class CircleOfCompetenceResult:
    status: str
    findings: tuple[str, ...]


@dataclass(frozen=True)
class OwnerEarningsAssessment:
    status: str
    owner_earnings: Decimal | None
    currency: str | None
    interpretation: str
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class ValuationAssessment:
    status: str
    selected_method: str | None
    current_price: Decimal | None
    fair_value: Decimal | None
    currency: str | None
    margin_of_safety: Decimal | None
    source_ids: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class EquityReviewResult:
    id: str
    calculation_version: str
    quality_model: str
    evidence_schema_version: str
    instrument_id: str
    as_of: str
    identity_status: str
    circle_of_competence: CircleOfCompetenceResult
    hard_screen_status: str
    criteria: tuple[CriterionAssessment, ...]
    points_awarded: Decimal
    points_available: Decimal
    score_percent: Decimal | None
    criteria_available: int
    criteria_total: int
    score_status: str
    quality_classification: str
    valuation: ValuationAssessment
    owner_earnings: OwnerEarningsAssessment
    source_assessments: tuple[SourceAssessment, ...]
    source_ids: tuple[str, ...]
    limitations: tuple[str, ...]
    conclusion: str
    proposed_next_actions: tuple[str, ...]
    mutation_performed: bool
