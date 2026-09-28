"""Deterministic individual-equity quality and valuation review."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
import re
from typing import Iterable

from .equity_models import (
    EQUITY_EVIDENCE_SCHEMA_VERSION,
    EQUITY_QUALITY_MODEL,
    EQUITY_REVIEW_VERSION,
    BooleanEvidence,
    CircleOfCompetenceResult,
    CriterionAssessment,
    DecimalEvidence,
    EquityReviewInput,
    EquityReviewResult,
    OwnerEarningsAssessment,
    ValuationAnchor,
    ValuationAssessment,
)
from .errors import ValidationError
from .models import PortfolioState, decimal_to_string
from .research_models import ResearchSource, SourceAssessment
from .validation import validate_state


_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_ISIN = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")
_MIC = re.compile(r"^[A-Z0-9]{4}$")
_CURRENCY = re.compile(r"^[A-Z]{3}$")
_VALUATION_PRIORITY = {"dcf": 0, "reverse_dcf": 1, "forward_pe": 2}
_CRITERIA_TOTAL = 8
_CRITERION_NAMES = frozenset(
    {
        "free_cash_flow",
        "debt_to_ebitda",
        "revenue_growth",
        "operating_margin",
        "capex_to_revenue",
        "institutional_ownership",
        "benchmark_outperformance",
        "moat_and_management",
    }
)


def _as_date(value: str, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValidationError(f"{field} must be an ISO date.") from error


def _as_datetime(value: str, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValidationError(f"{field} must be an ISO date-time.") from error
    if parsed.tzinfo is None:
        raise ValidationError(f"{field} must include a timezone.")
    return parsed


def _normalize_name(value: str) -> str:
    return " ".join(value.casefold().split())


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _validate_source(source: ResearchSource, review_date: date) -> None:
    if not _IDENTIFIER.fullmatch(source.id):
        raise ValidationError("Research source id is invalid.")
    if not source.provider.strip() or not source.reference.strip():
        raise ValidationError("Research source provider and reference are required.")
    source_date = _as_date(source.as_of, "sources[].as_of")
    retrieved = _as_datetime(source.retrieved_at, "sources[].retrieved_at")
    if source_date > review_date or retrieved.date() > review_date:
        raise ValidationError("Research source cannot be newer than the review date.")
    if retrieved.date() < source_date:
        raise ValidationError("Research retrieval cannot predate its value date.")
    if source.freshness_days < 0:
        raise ValidationError("Research source freshness_days cannot be negative.")
    if not source.methodology.strip() or not source.terms_reference.strip():
        raise ValidationError("Research source methodology and terms are required.")


def _validate_sourced_date(
    as_of: str,
    source_id: str,
    field: str,
    review_date: date,
    sources: dict[str, ResearchSource],
) -> None:
    observed = _as_date(as_of, field)
    if observed > review_date:
        raise ValidationError(f"{field} cannot be newer than the review date.")
    source = sources.get(source_id)
    if source is None:
        raise ValidationError(f"{field} references an unknown research source.")
    if observed > _as_date(source.as_of, "sources[].as_of"):
        raise ValidationError(f"{field} cannot be newer than its source.")


def _validate_decimal_evidence(
    item: DecimalEvidence | None,
    field: str,
    review_date: date,
    sources: dict[str, ResearchSource],
) -> None:
    if item is None:
        return
    if not item.value.is_finite():
        raise ValidationError(f"{field}.value must be finite.")
    _validate_sourced_date(item.as_of, item.source_id, f"{field}.as_of", review_date, sources)


def _validate_boolean_evidence(
    item: BooleanEvidence | None,
    field: str,
    review_date: date,
    sources: dict[str, ResearchSource],
) -> None:
    if item is None:
        return
    if not item.rationale.strip():
        raise ValidationError(f"{field}.rationale cannot be empty.")
    _validate_sourced_date(item.as_of, item.source_id, f"{field}.as_of", review_date, sources)


def _validate_identity(
    state: PortfolioState,
    review_input: EquityReviewInput,
    sources: dict[str, ResearchSource],
) -> None:
    identity = review_input.identity
    instruments = {instrument.id: instrument for instrument in state.instruments}
    instrument = instruments.get(identity.instrument_id)
    if instrument is None:
        raise ValidationError("Identity evidence references an unknown instrument.")
    if instrument.kind != "stock":
        raise ValidationError("Individual-equity review requires a stock instrument.")
    if identity.source_id not in sources:
        raise ValidationError("Identity evidence references an unknown research source.")
    if instrument.isin is None:
        raise ValidationError("Individual-equity review requires a recorded ISIN.")
    if not _ISIN.fullmatch(identity.isin) or identity.isin != instrument.isin:
        raise ValidationError("Reported ISIN does not match the portfolio instrument.")
    if _normalize_name(identity.reported_name) != _normalize_name(instrument.name):
        raise ValidationError("Reported instrument name does not match the portfolio instrument.")

    listing_fields = (
        identity.listing_id,
        identity.mic,
        identity.ticker,
        identity.trading_currency,
    )
    if any(item is not None for item in listing_fields) and not all(
        item is not None for item in listing_fields
    ):
        raise ValidationError("Listing identity fields must be supplied together.")
    if identity.listing_id is None:
        return
    listings = {listing.id: listing for listing in state.listings}
    listing = listings.get(identity.listing_id)
    if listing is None or listing.instrument_id != instrument.id:
        raise ValidationError("Reported listing does not belong to the portfolio instrument.")
    if not _MIC.fullmatch(identity.mic or ""):
        raise ValidationError("Reported listing MIC is invalid.")
    if not _CURRENCY.fullmatch(identity.trading_currency or ""):
        raise ValidationError("Reported listing currency is invalid.")
    if (
        identity.mic != listing.mic
        or identity.ticker != listing.ticker
        or identity.trading_currency != listing.trading_currency
    ):
        raise ValidationError("Reported listing identity does not match the portfolio listing.")


def _circle_result(review_input: EquityReviewInput) -> CircleOfCompetenceResult:
    evidence = review_input.circle_of_competence
    findings: list[str] = []
    if evidence.business_model_understood:
        if not evidence.business_model_summary.strip():
            raise ValidationError("A business-model summary is required when marked understood.")
        findings.append(evidence.business_model_summary.strip())
    else:
        findings.append("The business model is not understood well enough to explain it plainly.")
    if evidence.revenue_drivers_understood:
        if not evidence.revenue_driver_summary.strip():
            raise ValidationError("A revenue-driver summary is required when marked understood.")
        findings.append(evidence.revenue_driver_summary.strip())
    else:
        findings.append(
            "The causes of a material revenue decline are not identifiable "
            "without guessing."
        )

    if evidence.external_dependency is not None:
        if not evidence.external_dependency.strip():
            raise ValidationError("external_dependency cannot be blank.")
        findings.append(f"External dependency: {evidence.external_dependency.strip()}")
        if evidence.observable_event is None or not evidence.observable_event.strip():
            findings.append("No observable event was supplied for the external dependency.")
            return CircleOfCompetenceResult("untracked_dependency", tuple(findings))
        findings.append(f"Observable event: {evidence.observable_event.strip()}")
    elif evidence.observable_event is not None:
        raise ValidationError("observable_event requires an external_dependency.")

    status = (
        "inside"
        if evidence.business_model_understood and evidence.revenue_drivers_understood
        else "limited"
    )
    return CircleOfCompetenceResult(status, tuple(findings))


def _criterion(
    name: str,
    points: Decimal,
    maximum: Decimal,
    observed: str,
    rationale: str,
    source_ids: tuple[str, ...],
) -> CriterionAssessment:
    return CriterionAssessment(
        criterion=name,
        status="scored",
        points_awarded=points,
        maximum_points=maximum,
        observed_value=observed,
        rationale=rationale,
        source_ids=source_ids,
    )


def _missing(name: str, maximum: str) -> CriterionAssessment:
    return CriterionAssessment(
        criterion=name,
        status="not_available",
        points_awarded=Decimal("0"),
        maximum_points=Decimal(maximum),
        observed_value=None,
        rationale=(
            "No attributable evidence was supplied; the criterion is excluded "
            "from the denominator."
        ),
        source_ids=(),
    )


def _decimal_criterion(
    name: str,
    evidence: DecimalEvidence | None,
    maximum: str,
    scoring,
) -> CriterionAssessment:
    if evidence is None:
        return _missing(name, maximum)
    points, rationale = scoring(evidence.value)
    return _criterion(
        name,
        points,
        Decimal(maximum),
        decimal_to_string(evidence.value),
        rationale,
        (evidence.source_id,),
    )


def _boolean_criterion(
    name: str,
    evidence: BooleanEvidence | None,
) -> CriterionAssessment:
    if evidence is None:
        return _missing(name, "1")
    return _criterion(
        name,
        Decimal("1") if evidence.value else Decimal("0"),
        Decimal("1"),
        "true" if evidence.value else "false",
        evidence.rationale,
        (evidence.source_id,),
    )


def _quality_criteria(review_input: EquityReviewInput) -> tuple[CriterionAssessment, ...]:
    quality = review_input.quality
    fcf = quality.free_cash_flow
    monotonic = all(left.value <= right.value for left, right in zip(fcf, fcf[1:]))
    all_positive = all(item.value > 0 for item in fcf)
    fcf_points = (
        Decimal("2")
        if len(fcf) >= 2 and monotonic and all_positive
        else Decimal("1")
    )
    fcf_rationale = (
        "The supplied positive free-cash-flow series is non-decreasing."
        if fcf_points == Decimal("2")
        else "Free cash flow is positive but not a non-decreasing multi-period series."
    )
    fcf_assessment = _criterion(
        "free_cash_flow",
        fcf_points,
        Decimal("2"),
        ", ".join(decimal_to_string(item.value) for item in fcf),
        fcf_rationale,
        _unique(item.source_id for item in fcf),
    )

    def debt(value: Decimal):
        if value < Decimal("2"):
            return Decimal("2"), "Debt/EBITDA is below 2x."
        if value <= Decimal("3"):
            return Decimal("1"), "Debt/EBITDA is between 2x and 3x."
        return Decimal("0"), "Debt/EBITDA exceeds 3x."

    def growth(value: Decimal):
        if value >= Decimal("0.10"):
            return Decimal("1.5"), "Revenue growth is at least 10%."
        if value >= Decimal("0.05"):
            return Decimal("1"), "Revenue growth is between 5% and 10%."
        return Decimal("0"), "Revenue growth is below 5%."

    def margin(value: Decimal):
        if value >= Decimal("0.10"):
            return Decimal("1.5"), "Operating margin is at least 10%."
        if value >= Decimal("0.05"):
            return Decimal("1"), "Operating margin is between 5% and 10%."
        return Decimal("0"), "Operating margin is below 5%."

    def capex(value: Decimal):
        if value < Decimal("0.15"):
            return Decimal("1"), "CapEx/revenue is below 15%."
        return Decimal("0"), "CapEx/revenue is at least 15%; inspect owner earnings."

    def institutions(value: Decimal):
        if value >= Decimal("0.50"):
            return Decimal("1"), "Institutional ownership is at least 50%."
        return Decimal("0"), "Institutional ownership is below 50%."

    return (
        fcf_assessment,
        _decimal_criterion("debt_to_ebitda", quality.debt_to_ebitda, "2", debt),
        _decimal_criterion("revenue_growth", quality.revenue_growth, "1.5", growth),
        _decimal_criterion("operating_margin", quality.operating_margin, "1.5", margin),
        _decimal_criterion("capex_to_revenue", quality.capex_to_revenue, "1", capex),
        _decimal_criterion(
            "institutional_ownership",
            quality.institutional_ownership,
            "1",
            institutions,
        ),
        _boolean_criterion("benchmark_outperformance", quality.benchmark_outperformance),
        _boolean_criterion("moat_and_management", quality.moat_and_management),
    )


def _owner_earnings(review_input: EquityReviewInput) -> OwnerEarningsAssessment:
    quality = review_input.quality
    if quality.capex_to_revenue is None:
        return OwnerEarningsAssessment(
            "unavailable",
            None,
            None,
            "CapEx/revenue is unavailable, so the adjustment trigger cannot be evaluated.",
            (),
        )
    if quality.capex_to_revenue.value < Decimal("0.15"):
        return OwnerEarningsAssessment(
            "not_required",
            None,
            None,
            "CapEx/revenue is below the adjustment threshold.",
            (quality.capex_to_revenue.source_id,),
        )
    evidence = quality.owner_earnings
    if evidence is None:
        return OwnerEarningsAssessment(
            "unavailable",
            None,
            None,
            "High CapEx requires maintenance-versus-growth evidence before interpretation.",
            (quality.capex_to_revenue.source_id,),
        )
    values = (
        evidence.reported_earnings,
        evidence.depreciation_and_amortization,
        evidence.maintenance_capex,
    )
    source_ids = _unique(
        item.source_id for item in values if item is not None
    )
    if any(item is None for item in values):
        return OwnerEarningsAssessment(
            "incomplete",
            None,
            evidence.currency,
            "Reported earnings, depreciation and amortization, and maintenance "
            "CapEx are all required.",
            source_ids,
        )
    reported, depreciation, maintenance = values
    assert reported is not None and depreciation is not None and maintenance is not None
    owner_earnings = reported.value + depreciation.value - maintenance.value
    funding = evidence.growth_capex_funded_from_fcf
    if funding is None:
        status = "calculated_with_limited_funding_evidence"
        interpretation = (
            "Owner earnings are calculated, but growth-capex funding evidence "
            "is missing."
        )
    elif funding.value:
        status = "growth_investment"
        interpretation = (
            "Growth CapEx is reported as funded from free cash flow; high CapEx "
            "is not automatically a red flag."
        )
        source_ids = _unique((*source_ids, funding.source_id))
    else:
        status = "funding_red_flag"
        interpretation = (
            "Growth CapEx is not reported as funded from free cash flow, which "
            "preserves the financing red flag."
        )
        source_ids = _unique((*source_ids, funding.source_id))
    return OwnerEarningsAssessment(
        status,
        owner_earnings,
        evidence.currency,
        interpretation,
        source_ids,
    )


def _valuation(anchors: tuple[ValuationAnchor, ...]) -> ValuationAssessment:
    if not anchors:
        return ValuationAssessment(
            "unavailable", None, None, None, None, None, (),
            ("No supported valuation anchor was supplied.",),
        )
    ordered = sorted(anchors, key=lambda item: _VALUATION_PRIORITY[item.method])
    selected = ordered[0]
    margins = tuple(
        (item.fair_value - item.current_price) / item.fair_value
        for item in ordered
    )
    directions = {margin >= 0 for margin in margins}
    selected_margin = margins[0]
    source_ids = _unique(
        source_id for item in ordered for source_id in item.source_ids
    )
    if len(directions) > 1:
        return ValuationAssessment(
            "conflicting",
            selected.method,
            selected.current_price,
            selected.fair_value,
            selected.currency,
            selected_margin,
            source_ids,
            (
                "Supported valuation methods disagree on whether price is above "
                "or below fair value; they were not averaged.",
            ),
        )
    if selected_margin >= Decimal("0.20"):
        status = "acceptable"
    elif selected_margin >= Decimal("0"):
        status = "limited"
    else:
        status = "premium"
    return ValuationAssessment(
        status,
        selected.method,
        selected.current_price,
        selected.fair_value,
        selected.currency,
        selected_margin,
        source_ids,
        (),
    )


def _source_assessments(
    sources: dict[str, ResearchSource],
    used_source_ids: tuple[str, ...],
    review_date: date,
) -> tuple[SourceAssessment, ...]:
    assessments: list[SourceAssessment] = []
    for source_id in sorted(used_source_ids):
        source = sources[source_id]
        age_days = (review_date - _as_date(source.as_of, "sources[].as_of")).days
        assessments.append(
            SourceAssessment(
                source_id=source.id,
                provider=source.provider,
                reference=source.reference,
                as_of=source.as_of,
                retrieved_at=source.retrieved_at,
                age_days=age_days,
                freshness="fresh" if age_days <= source.freshness_days else "stale",
                methodology=source.methodology,
                limitations=source.limitations,
                terms_reference=source.terms_reference,
                cache_permitted=source.cache_permitted,
                redistribution_permitted=source.redistribution_permitted,
            )
        )
    return tuple(assessments)


def _validate_input(state: PortfolioState, review_input: EquityReviewInput) -> None:
    if review_input.schema_version != EQUITY_EVIDENCE_SCHEMA_VERSION:
        raise ValidationError("Unsupported equity evidence schema version.")
    review_date = _as_date(review_input.as_of, "as_of")
    if not review_input.sources:
        raise ValidationError("Equity review requires at least one research source.")
    if len({source.id for source in review_input.sources}) != len(review_input.sources):
        raise ValidationError("Research source identifiers must be unique.")
    sources = {source.id: source for source in review_input.sources}
    for source in review_input.sources:
        _validate_source(source, review_date)
    _validate_identity(state, review_input, sources)

    quality = review_input.quality
    periods = [item.period_end for item in quality.free_cash_flow]
    if periods != sorted(periods) or len(periods) != len(set(periods)):
        raise ValidationError("Free-cash-flow observations must be unique and chronological.")
    for item in quality.free_cash_flow:
        if not item.value.is_finite():
            raise ValidationError("Free-cash-flow values must be finite.")
        _validate_sourced_date(
            item.period_end,
            item.source_id,
            "quality.free_cash_flow[].period_end",
            review_date,
            sources,
        )
    decimal_fields = (
        (quality.debt_to_ebitda, "quality.debt_to_ebitda"),
        (quality.revenue_growth, "quality.revenue_growth"),
        (quality.operating_margin, "quality.operating_margin"),
        (quality.capex_to_revenue, "quality.capex_to_revenue"),
        (quality.institutional_ownership, "quality.institutional_ownership"),
    )
    for item, field in decimal_fields:
        _validate_decimal_evidence(item, field, review_date, sources)
    if quality.institutional_ownership is not None and not (
        Decimal("0") <= quality.institutional_ownership.value <= Decimal("1")
    ):
        raise ValidationError("Institutional ownership must be between zero and one.")
    if quality.capex_to_revenue is not None and quality.capex_to_revenue.value < 0:
        raise ValidationError("CapEx/revenue cannot be negative.")
    if quality.debt_to_ebitda is not None and quality.debt_to_ebitda.value < 0:
        raise ValidationError(
            "Debt/EBITDA cannot be negative; use unavailable for a non-meaningful ratio."
        )
    _validate_boolean_evidence(
        quality.benchmark_outperformance,
        "quality.benchmark_outperformance",
        review_date,
        sources,
    )
    _validate_boolean_evidence(
        quality.moat_and_management,
        "quality.moat_and_management",
        review_date,
        sources,
    )
    owner = quality.owner_earnings
    if owner is not None:
        if not _CURRENCY.fullmatch(owner.currency):
            raise ValidationError("Owner-earnings currency must be an uppercase ISO code.")
        owner_components = (
            (owner.reported_earnings, "quality.owner_earnings.reported_earnings"),
            (
                owner.depreciation_and_amortization,
                "quality.owner_earnings.depreciation_and_amortization",
            ),
            (owner.maintenance_capex, "quality.owner_earnings.maintenance_capex"),
        )
        for item, field in owner_components:
            _validate_decimal_evidence(item, field, review_date, sources)
        component_dates = {
            item.as_of for item, _ in owner_components if item is not None
        }
        if len(component_dates) > 1:
            raise ValidationError(
                "Owner-earnings components must use the same reporting date."
            )
        if (
            owner.depreciation_and_amortization is not None
            and owner.depreciation_and_amortization.value < 0
        ):
            raise ValidationError(
                "Owner-earnings depreciation and amortization cannot be negative."
            )
        if owner.maintenance_capex is not None and owner.maintenance_capex.value < 0:
            raise ValidationError("Owner-earnings maintenance CapEx cannot be negative.")
        _validate_boolean_evidence(
            owner.growth_capex_funded_from_fcf,
            "quality.owner_earnings.growth_capex_funded_from_fcf",
            review_date,
            sources,
        )

    methods: set[str] = set()
    for anchor in review_input.valuation_anchors:
        if anchor.method not in _VALUATION_PRIORITY:
            raise ValidationError("Unsupported valuation method.")
        if anchor.method in methods:
            raise ValidationError("Only one valuation anchor is allowed per method.")
        methods.add(anchor.method)
        if (
            not anchor.current_price.is_finite()
            or not anchor.fair_value.is_finite()
            or anchor.current_price <= 0
            or anchor.fair_value <= 0
        ):
            raise ValidationError("Valuation prices must be positive and finite.")
        if not _CURRENCY.fullmatch(anchor.currency):
            raise ValidationError("Valuation currency must be an uppercase ISO code.")
        if not anchor.rationale.strip() or not anchor.source_ids:
            raise ValidationError("A valuation anchor requires rationale and sources.")
        if len(set(anchor.source_ids)) != len(anchor.source_ids):
            raise ValidationError("Valuation source identifiers must be unique.")
        for source_id in anchor.source_ids:
            _validate_sourced_date(
                anchor.as_of,
                source_id,
                "valuation_anchors[].as_of",
                review_date,
                sources,
            )
    currencies = {anchor.currency for anchor in review_input.valuation_anchors}
    if len(currencies) > 1:
        raise ValidationError("Valuation anchors must use one currency.")
    anchor_dates = {anchor.as_of for anchor in review_input.valuation_anchors}
    current_prices = {anchor.current_price for anchor in review_input.valuation_anchors}
    if len(anchor_dates) > 1 or len(current_prices) > 1:
        raise ValidationError(
            "Valuation anchors must use one as-of date and current price."
        )


def review_equity(
    state: PortfolioState,
    review_input: EquityReviewInput,
) -> EquityReviewResult:
    """Review one identified stock without live retrieval, execution, or mutation."""

    validate_state(state)
    _validate_input(state, review_input)
    review_date = _as_date(review_input.as_of, "as_of")
    sources = {source.id: source for source in review_input.sources}
    circle = _circle_result(review_input)
    limitations: list[str] = []

    fcf = review_input.quality.free_cash_flow
    if not fcf:
        hard_screen = "insufficient"
        criteria: tuple[CriterionAssessment, ...] = ()
        limitations.append("Positive free cash flow is a required hard-screen input.")
    elif fcf[-1].value <= 0:
        hard_screen = "failed"
        criteria = ()
        limitations.append("The latest supplied free cash flow is not positive.")
    else:
        hard_screen = "passed"
        criteria = _quality_criteria(review_input)

    scored = tuple(item for item in criteria if item.status == "scored")
    points_awarded = sum((item.points_awarded for item in scored), Decimal("0"))
    points_available = sum((item.maximum_points for item in scored), Decimal("0"))
    score_percent = (
        (points_awarded / points_available * Decimal("100")).quantize(
            Decimal("0.1"), rounding=ROUND_HALF_UP
        )
        if points_available > 0
        else None
    )
    criteria_available = len(scored)
    missing_count = _CRITERIA_TOTAL - criteria_available
    debt_missing = review_input.quality.debt_to_ebitda is None
    if debt_missing:
        limitations.append("Debt/EBITDA is required before threshold classification.")
    if hard_screen != "passed":
        score_status = "not_scored"
        classification = "not_applied"
    elif missing_count >= 3 or debt_missing:
        score_status = "incomplete"
        classification = "not_applied"
        if missing_count >= 3:
            limitations.append("Three or more quality criteria are unavailable.")
    else:
        score_status = "complete"
        assert score_percent is not None
        if score_percent >= Decimal("72"):
            classification = "quality"
        elif score_percent >= Decimal("55"):
            classification = "mid_tier"
        else:
            classification = "exit_zone"

    valuation = _valuation(review_input.valuation_anchors)
    owner_earnings = _owner_earnings(review_input)
    decision_source_ids = _unique(
        (
            *(item.source_id for item in fcf),
            *(source_id for item in criteria for source_id in item.source_ids),
            *valuation.source_ids,
            *owner_earnings.source_ids,
        )
    )
    used_source_ids = _unique(
        (review_input.identity.source_id, *decision_source_ids)
    )
    source_assessments = _source_assessments(sources, used_source_ids, review_date)
    for source in source_assessments:
        limitations.extend(source.limitations)
        if source.freshness == "stale":
            limitations.append(f"Research source {source.source_id} is stale.")
    stale_decision_sources = tuple(
        source.source_id
        for source in source_assessments
        if source.source_id in decision_source_ids and source.freshness == "stale"
    )

    if stale_decision_sources:
        conclusion = "insufficient_evidence"
        next_actions = (
            "Refresh stale evidence before applying the quality or valuation "
            "conclusion.",
        )
    elif hard_screen == "failed":
        conclusion = "hard_screen_failed"
        next_actions = (
            "Do not apply the quality thresholds while free cash flow is "
            "non-positive.",
        )
    elif hard_screen != "passed" or score_status != "complete":
        conclusion = "insufficient_evidence"
        next_actions = ("Obtain the missing required evidence before making a quality conclusion.",)
    elif circle.status == "untracked_dependency":
        conclusion = "insufficient_evidence"
        next_actions = (
            "Define an observable event for the external dependency before "
            "relying on the review.",
        )
    elif classification == "exit_zone":
        conclusion = "quality_below_threshold"
        next_actions = ("Do not treat the instrument as a quality candidate under this model.",)
    elif classification == "mid_tier":
        conclusion = "watch"
        next_actions = ("Keep the instrument under observation; no transaction is proposed.",)
    elif owner_earnings.status == "funding_red_flag":
        conclusion = "funding_red_flag"
        next_actions = (
            "Do not treat the instrument as eligible while growth CapEx is not "
            "funded from free cash flow.",
        )
    elif valuation.status in {"conflicting", "unavailable"}:
        conclusion = "insufficient_valuation"
        next_actions = (
            "Resolve or obtain a supported valuation anchor before considering "
            "an entry.",
        )
    elif circle.status == "limited":
        conclusion = "limited_competence"
        next_actions = (
            "Treat the quality result with reduced decision confidence; no "
            "transaction is proposed.",
        )
    elif valuation.status == "premium":
        conclusion = "quality_at_premium"
        next_actions = (
            "The business passes the quality model, but the selected valuation "
            "anchor shows a premium.",
        )
    elif valuation.status == "limited":
        conclusion = "limited_margin"
        next_actions = ("The business passes the quality model with limited margin of safety.",)
    else:
        conclusion = "eligible_for_consideration"
        next_actions = ("The evidence supports further consideration, not trade execution.",)

    return EquityReviewResult(
        id=f"equity-review:{review_input.identity.instrument_id}:{review_input.as_of}",
        calculation_version=EQUITY_REVIEW_VERSION,
        quality_model=EQUITY_QUALITY_MODEL,
        evidence_schema_version=review_input.schema_version,
        instrument_id=review_input.identity.instrument_id,
        as_of=review_input.as_of,
        identity_status="matched",
        circle_of_competence=circle,
        hard_screen_status=hard_screen,
        criteria=criteria,
        points_awarded=points_awarded,
        points_available=points_available,
        score_percent=score_percent,
        criteria_available=criteria_available,
        criteria_total=_CRITERIA_TOTAL,
        score_status=score_status,
        quality_classification=classification,
        valuation=valuation,
        owner_earnings=owner_earnings,
        source_assessments=source_assessments,
        source_ids=tuple(sorted(used_source_ids)),
        limitations=_unique(limitations),
        conclusion=conclusion,
        proposed_next_actions=next_actions,
        mutation_performed=False,
    )


def validate_equity_review_result(result: EquityReviewResult) -> None:
    """Reject inconsistent constructed results before private persistence."""

    if result.calculation_version != EQUITY_REVIEW_VERSION:
        raise ValidationError("Unsupported equity review calculation version.")
    if result.evidence_schema_version != EQUITY_EVIDENCE_SCHEMA_VERSION:
        raise ValidationError("Unsupported equity evidence schema version in result.")
    if result.quality_model != EQUITY_QUALITY_MODEL:
        raise ValidationError("Unsupported equity quality model.")
    _as_date(result.as_of, "equity_review.as_of")
    if result.identity_status != "matched" or result.mutation_performed:
        raise ValidationError("Equity review identity or mutation status is invalid.")
    if result.criteria_total != _CRITERIA_TOTAL:
        raise ValidationError("Equity review criterion total is invalid.")

    names = [item.criterion for item in result.criteria]
    if len(set(names)) != len(names) or not set(names) <= _CRITERION_NAMES:
        raise ValidationError("Equity review criteria are invalid or duplicated.")
    if result.criteria and set(names) != _CRITERION_NAMES:
        raise ValidationError("A scored equity review must expose all criteria.")
    scored = tuple(item for item in result.criteria if item.status == "scored")
    if any(item.status not in {"scored", "not_available"} for item in result.criteria):
        raise ValidationError("Equity review criterion status is invalid.")
    if result.criteria_available != len(scored):
        raise ValidationError("Equity review available-criterion count is inconsistent.")
    points_awarded = sum((item.points_awarded for item in scored), Decimal("0"))
    points_available = sum((item.maximum_points for item in scored), Decimal("0"))
    if (
        result.points_awarded != points_awarded
        or result.points_available != points_available
    ):
        raise ValidationError("Equity review point totals are inconsistent.")
    expected_percent = (
        (points_awarded / points_available * Decimal("100")).quantize(
            Decimal("0.1"), rounding=ROUND_HALF_UP
        )
        if points_available > 0
        else None
    )
    if result.score_percent != expected_percent:
        raise ValidationError("Equity review percentage is inconsistent.")
    assessment_ids = tuple(
        sorted(item.source_id for item in result.source_assessments)
    )
    if len(set(assessment_ids)) != len(assessment_ids):
        raise ValidationError("Equity review source assessments are duplicated.")
    if tuple(sorted(result.source_ids)) != assessment_ids:
        raise ValidationError("Equity review source identifiers are inconsistent.")
