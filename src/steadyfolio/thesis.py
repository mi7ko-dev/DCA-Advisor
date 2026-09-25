"""Deterministic, non-mutating investment-thesis review."""

from __future__ import annotations

from datetime import date
from typing import Sequence

from .errors import ValidationError
from .models import PortfolioState
from .research_models import (
    INTELLIGENCE_CALCULATION_VERSION,
    ResearchSnapshot,
    SourceAssessment,
    ThesisEvidence,
    ThesisReviewResult,
)
from .research_validation import validate_research_snapshot
from .validation import validate_state


def _as_date(value: str, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValidationError(f"{field} must be an ISO date.") from error


def review_investment_thesis(
    state: PortfolioState,
    thesis_id: str,
    evidence: Sequence[ThesisEvidence],
    observed_review_triggers: Sequence[str],
    reviewed_at: str,
    snapshot: ResearchSnapshot,
) -> ThesisReviewResult:
    """Propose a review action without changing holdings, targets, or the thesis."""

    validate_state(state)
    validate_research_snapshot(snapshot)
    review_date = _as_date(reviewed_at, "reviewed_at")
    thesis_by_id = {thesis.id: thesis for thesis in state.investment_theses}
    thesis = thesis_by_id.get(thesis_id)
    if thesis is None:
        raise ValidationError("The requested investment thesis does not exist.")

    if len({item.id for item in evidence}) != len(evidence):
        raise ValidationError("Thesis evidence identifiers must be unique.")
    sources = {source.id: source for source in snapshot.sources}
    configured = set(thesis.review_triggers)
    trigger_hits = [
        trigger for trigger in observed_review_triggers if trigger in configured
    ]
    if len(set(observed_review_triggers)) != len(observed_review_triggers):
        raise ValidationError("Observed review triggers must be unique.")
    if thesis.review_date is not None and _as_date(
        thesis.review_date, "investment_thesis.review_date"
    ) <= review_date:
        trigger_hits.append("Scheduled review date reached")

    facts: list[str] = []
    interpretations: list[str] = []
    limitations: list[str] = []
    source_ids: set[str] = set()
    non_price_contradiction = False
    for item in evidence:
        if item.instrument_id != thesis.instrument_id:
            raise ValidationError("Thesis evidence references a different instrument.")
        if item.assessment not in {"supports", "neutral", "contradicts"}:
            raise ValidationError("Unknown thesis evidence assessment.")
        if _as_date(item.observed_at, "thesis_evidence[].observed_at") > review_date:
            raise ValidationError("Thesis evidence cannot be newer than the review date.")
        source = sources.get(item.source_id)
        if source is None:
            raise ValidationError("Thesis evidence references an unknown research source.")
        source_date = _as_date(source.as_of, "research_source.as_of")
        if source_date > review_date:
            raise ValidationError("Thesis evidence source cannot be newer than the review date.")
        if _as_date(item.observed_at, "thesis_evidence[].observed_at") > source_date:
            raise ValidationError("Thesis evidence cannot be newer than its source.")
        source_ids.add(item.source_id)
        facts.append(
            f"{item.summary} (source {item.source_id}, observed {item.observed_at})"
        )
        limitations.extend(item.limitations)
        limitations.extend(source.limitations)
        if item.assessment == "supports":
            interpretations.append(f"Evidence {item.id} supports the current rationale.")
        elif item.assessment == "neutral":
            interpretations.append(f"Evidence {item.id} is neutral to the current rationale.")
        elif item.kind == "price_change":
            interpretations.append(
                f"Evidence {item.id} is a price change; price movement alone is not thesis failure."
            )
        else:
            non_price_contradiction = True
            interpretations.append(
                f"Evidence {item.id} contradicts a non-price part of the current rationale."
            )

    unmatched = sorted(set(observed_review_triggers) - configured)
    if unmatched:
        limitations.append(
            "Observed events outside the configured trigger set require manual interpretation."
        )

    if not evidence:
        proposed_action = "investigate"
        proposed_changes = (
            "Obtain current, attributable evidence before deciding whether the thesis should change.",
        )
        limitations.append("No evidence was supplied for this review.")
    elif trigger_hits or non_price_contradiction:
        proposed_action = "review"
        proposed_changes = (
            "Review the thesis and any policy change with the user; do not mutate holdings or targets automatically.",
        )
    else:
        proposed_action = "retain"
        proposed_changes = (
            "Retain the current thesis pending its next review; no portfolio mutation is proposed.",
        )

    source_assessments: list[SourceAssessment] = []
    for source_id in sorted(source_ids):
        source = sources[source_id]
        age_days = (review_date - _as_date(source.as_of, "research_source.as_of")).days
        freshness = "fresh" if age_days <= source.freshness_days else "stale"
        if freshness == "stale":
            limitations.append(
                f"Research source {source.id} is stale at {age_days} days old."
            )
        source_assessments.append(
            SourceAssessment(
                source_id=source.id,
                provider=source.provider,
                reference=source.reference,
                as_of=source.as_of,
                retrieved_at=source.retrieved_at,
                age_days=age_days,
                freshness=freshness,
                methodology=source.methodology,
                limitations=source.limitations,
                terms_reference=source.terms_reference,
                cache_permitted=source.cache_permitted,
                redistribution_permitted=source.redistribution_permitted,
            )
        )

    return ThesisReviewResult(
        id=f"thesis-review:{thesis.id}:{reviewed_at}",
        calculation_version=INTELLIGENCE_CALCULATION_VERSION,
        thesis_id=thesis.id,
        instrument_id=thesis.instrument_id,
        reviewed_at=reviewed_at,
        role=thesis.role,
        rationale=thesis.rationale,
        target_weight=thesis.target_weight,
        target_range_min=thesis.target_range_min,
        target_range_max=thesis.target_range_max,
        benchmark_instrument_id=thesis.benchmark_instrument_id,
        risks=thesis.risks,
        last_review_date=thesis.last_review_date,
        next_review_date=thesis.review_date,
        configured_review_triggers=thesis.review_triggers,
        evidence_facts=tuple(facts),
        interpretations=tuple(interpretations),
        triggered_review_conditions=tuple(dict.fromkeys(trigger_hits)),
        proposed_action=proposed_action,
        proposed_changes=proposed_changes,
        source_assessments=tuple(source_assessments),
        source_ids=tuple(sorted(source_ids)),
        limitations=tuple(dict.fromkeys(limitations)),
    )
