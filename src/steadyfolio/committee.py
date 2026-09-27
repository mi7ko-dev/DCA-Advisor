"""Bounded routing and sequential review lenses over deterministic engine results."""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re
from typing import Mapping, Sequence

from .calculations import analyze_portfolio, plan_contribution
from .committee_models import (
    COMMITTEE_VERSION,
    CommitteeRequest,
    CommitteeResult,
    SourceDisclosure,
    SpecialistInterpretation,
    WorkflowTrace,
)
from .errors import ProviderUnavailableError, ValidationError
from .intelligence import analyze_portfolio_intelligence
from .models import (
    AnalysisResult,
    FxRate,
    MarketPrice,
    PortfolioState,
    TradingConstraint,
    decimal_to_string,
)
from .providers import ResearchProvider
from .research_models import (
    PortfolioIntelligenceResult,
    ResearchRequest,
    ResearchSnapshot,
    StressWindow,
    ThesisEvidence,
    ThesisReviewResult,
)
from .thesis import review_investment_thesis


_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_AMOUNT = re.compile(
    r"\b(?P<currency>[A-Z]{3})\s*(?P<amount>[0-9]+(?:[.,][0-9]{1,2})?)\b"
)
_EXECUTION_MODE = (
    "deterministic engine with sequential review lenses; no independent agents"
)


def committee_request_from_message(
    request_id: str,
    message: str,
    as_of: str,
    *,
    instrument_id: str | None = None,
    thesis_id: str | None = None,
) -> CommitteeRequest:
    """Create a structured request and parse only an explicit currency-first amount."""

    match = _AMOUNT.search(message)
    amount: Decimal | None = None
    currency: str | None = None
    if match:
        try:
            amount = Decimal(match.group("amount").replace(",", "."))
        except InvalidOperation as error:
            raise ValidationError("The contribution amount is not a valid decimal.") from error
        currency = match.group("currency")
    return CommitteeRequest(
        id=request_id,
        message=message,
        as_of=as_of,
        contribution_amount=amount,
        contribution_currency=currency,
        instrument_id=instrument_id,
        thesis_id=thesis_id,
    )


def route_request(request: CommitteeRequest) -> str:
    """Route a narrow conversational request without invoking research or arithmetic."""

    _validate_request(request)
    normalized = " ".join(request.message.lower().split())
    if "overlap" in normalized or "overlapping" in normalized:
        return "overlap_review"
    if (
        request.thesis_id is not None
        or request.instrument_id is not None
        or "still be in my portfolio" in normalized
        or "investment thesis" in normalized
    ):
        return "thesis_review"
    if "review" in normalized and "portfolio" in normalized:
        return "portfolio_review"
    if request.contribution_amount is not None or any(
        phrase in normalized
        for phrase in ("to invest this month", "monthly contribution", "contribute")
    ):
        return "contribution"
    return "clarification"


def _validate_request(request: CommitteeRequest) -> None:
    if not _IDENTIFIER.fullmatch(request.id):
        raise ValidationError("Committee request id is invalid.")
    if not request.message.strip():
        raise ValidationError("Committee request message cannot be empty.")
    try:
        date.fromisoformat(request.as_of)
    except ValueError as error:
        raise ValidationError("Committee request as_of must be an ISO date.") from error
    if request.contribution_amount is not None and (
        request.contribution_amount <= 0
        or not request.contribution_amount.is_finite()
    ):
        raise ValidationError("Contribution amount must be positive and finite.")
    if request.contribution_currency is not None and not re.fullmatch(
        r"[A-Z]{3}", request.contribution_currency
    ):
        raise ValidationError("Contribution currency must be an uppercase ISO code.")
    if request.contribution_method not in {"simple", "drift_aware"}:
        raise ValidationError("Contribution method is unsupported.")
    if request.max_research_passes not in (0, 1):
        raise ValidationError("At most one research pass is allowed.")
    if request.max_critic_passes not in (0, 1):
        raise ValidationError("At most one critic pass is allowed.")
    if request.max_revisions not in (0, 1):
        raise ValidationError("At most one revision is allowed.")
    if request.max_external_calls != 0:
        raise ValidationError("Phase 5 does not permit live external calls.")


def _percent(value: Decimal) -> str:
    rendered = (value * Decimal("100")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    return f"{rendered}%"


def _money(value: Decimal, currency: str) -> str:
    rendered = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{rendered} {currency}"


def _unique(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


def _market_sources(
    state: PortfolioState, source_ids: Sequence[str], as_of: str
) -> tuple[SourceDisclosure, ...]:
    cutoff = date.fromisoformat(as_of)
    selected = {source_id for source_id in source_ids}
    disclosures: list[SourceDisclosure] = []
    for source in state.data_sources:
        if source.id not in selected:
            continue
        try:
            source_date = date.fromisoformat(source.value_time[:10])
        except ValueError:
            freshness = "unknown"
            limitations = ("The market source value time could not be dated.",)
        else:
            age_days = (cutoff - source_date).days
            freshness = "fresh" if age_days <= 1 else "stale"
            limitations = (
                ()
                if freshness == "fresh"
                else (f"The market source is {age_days} days old at review time.",)
            )
        disclosures.append(
            SourceDisclosure(
                source_id=source.id,
                provider=source.provider,
                reference=source.reference,
                value_time=source.value_time,
                retrieved_at=source.retrieved_at,
                freshness=freshness,
                limitations=limitations,
            )
        )
    return tuple(disclosures)


def _research_sources(
    result: PortfolioIntelligenceResult | ThesisReviewResult,
) -> tuple[SourceDisclosure, ...]:
    return tuple(
        SourceDisclosure(
            source_id=item.source_id,
            provider=item.provider,
            reference=item.reference,
            value_time=item.as_of,
            retrieved_at=item.retrieved_at,
            freshness=item.freshness,
            limitations=item.limitations,
        )
        for item in result.source_assessments
    )


def _combine_sources(
    *groups: Sequence[SourceDisclosure],
) -> tuple[SourceDisclosure, ...]:
    selected: dict[str, SourceDisclosure] = {}
    for group in groups:
        for source in group:
            selected[source.source_id] = source
    return tuple(selected[source_id] for source_id in sorted(selected))


def _analysis_facts(analysis: AnalysisResult) -> tuple[str, ...]:
    facts = [
        f"Portfolio value is {_money(analysis.total_value, analysis.base_currency)} on {analysis.valuation_date}.",
        f"Weighted annual fee rate is {_percent(analysis.weighted_annual_fee_rate)}.",
    ]
    facts.extend(
        f"{position.instrument_id}: current {_percent(position.current_weight)}, "
        f"approved target {_percent(position.target_weight)}, signed drift {_percent(position.drift)}."
        for position in analysis.positions
    )
    return tuple(facts)


def _fetch_research(
    request: CommitteeRequest,
    state: PortfolioState,
    provider: ResearchProvider | None,
) -> tuple[ResearchSnapshot | None, int, tuple[str, ...]]:
    if provider is None or request.max_research_passes == 0:
        return None, 0, ("No structured research snapshot was supplied.",)
    try:
        snapshot = provider.fetch(
            ResearchRequest(
                instrument_ids=tuple(item.id for item in state.instruments),
                listing_ids=tuple(item.id for item in state.listings),
                as_of=request.as_of,
            )
        )
    except ProviderUnavailableError:
        return None, 1, ("The research provider was unavailable.",)
    return snapshot, 1, ()


def _clarification_result(request: CommitteeRequest, route: str) -> CommitteeResult:
    missing = "The request does not identify a supported workflow."
    if route == "contribution":
        missing = "A contribution amount and currency are required."
    elif route == "thesis_review":
        missing = "An instrument and an active thesis are required for thesis review."
    return CommitteeResult(
        id=f"committee:{request.id}:{request.as_of}",
        committee_version=COMMITTEE_VERSION,
        request_id=request.id,
        request_text=request.message,
        route=route,
        status="needs_clarification",
        as_of=request.as_of,
        deterministic_facts=(),
        sources=(),
        data_limitations=(missing,),
        assumptions=(),
        specialist_interpretations=(),
        disagreements=(),
        final_synthesis=missing,
        proposed_next_actions=("Provide the missing structured input; no action was taken.",),
        requires_user_approval=False,
        approval_reasons=(),
        mutation_performed=False,
        trace=WorkflowTrace(
            route=route,
            deterministic_tools=(),
            review_lenses=(),
            provider_calls=0,
            external_calls=0,
            critic_passes=0,
            revisions=0,
            execution_mode=_EXECUTION_MODE,
        ),
    )


def _run_contribution(
    request: CommitteeRequest,
    state: PortfolioState,
    prices: Sequence[MarketPrice],
    fx_rates: Sequence[FxRate],
    constraints: Sequence[TradingConstraint],
    preferred_listings: Mapping[str, str] | None,
) -> CommitteeResult:
    if request.contribution_amount is None or request.contribution_currency is None:
        return _clarification_result(request, "contribution")
    analysis = analyze_portfolio(state, prices, fx_rates, request.as_of)
    plan = plan_contribution(
        state,
        analysis,
        prices,
        fx_rates,
        request.contribution_amount,
        request.contribution_currency,
        request.contribution_method,
        request.as_of,
        constraints,
        preferred_listings,
    )
    facts = list(_analysis_facts(analysis))
    facts.extend(
        (
            f"Proposed purchases total {_money(plan.total_purchase_value, plan.currency)}.",
            f"Estimated costs total {_money(plan.total_estimated_trade_cost, plan.currency)}.",
            f"Residual cash is {_money(plan.remaining_cash, plan.currency)}.",
        )
    )
    for line in plan.lines:
        if line.proposed_contribution > 0:
            facts.append(
                f"Proposed buy for {line.instrument_id}: quantity "
                f"{decimal_to_string(line.quantity)}, value "
                f"{_money(line.proposed_contribution, plan.currency)}, remaining drift "
                f"{_percent(line.remaining_drift)}."
            )
    limitations = _unique((*analysis.warnings, *plan.warnings))
    approval_reasons = (
        "Executing or recording a real transaction requires explicit user approval.",
    )
    return CommitteeResult(
        id=f"committee:{request.id}:{request.as_of}",
        committee_version=COMMITTEE_VERSION,
        request_id=request.id,
        request_text=request.message,
        route="contribution",
        status="limited" if limitations else "complete",
        as_of=request.as_of,
        deterministic_facts=tuple(facts),
        sources=_market_sources(state, plan.source_ids, request.as_of),
        data_limitations=limitations,
        assumptions=(
            f"The approved target remains policy and the method is {plan.method}.",
            "Prices, FX, fees, and trading constraints are supplied inputs, not forecasts.",
        ),
        specialist_interpretations=(),
        disagreements=(),
        final_synthesis=(
            "The buy-only plan uses the available contribution without selling or "
            "mutating portfolio state. Any remaining drift stays visible."
        ),
        proposed_next_actions=(
            "Review the proposal and its source dates.",
            "Approve separately before placing or recording any real transaction.",
        ),
        requires_user_approval=plan.total_purchase_value > 0,
        approval_reasons=approval_reasons,
        mutation_performed=False,
        trace=WorkflowTrace(
            route="contribution",
            deterministic_tools=("analyze_portfolio", "plan_contribution"),
            review_lenses=(),
            provider_calls=0,
            external_calls=0,
            critic_passes=0,
            revisions=0,
            execution_mode=_EXECUTION_MODE,
        ),
    )


def _portfolio_lenses(
    analysis: AnalysisResult,
    intelligence: PortfolioIntelligenceResult | None,
) -> tuple[SpecialistInterpretation, ...]:
    largest_drift = max(analysis.positions, key=lambda item: abs(item.drift))
    allocation = SpecialistInterpretation(
        role="allocation-diversification",
        conclusion="act_within_approved_policy",
        interpretation=(
            f"The largest signed drift is {largest_drift.instrument_id} at "
            f"{_percent(largest_drift.drift)}; policy-preserving new contributions "
            "can reduce drift without selling."
        ),
        evidence_references=(analysis.id,),
        limitations=("This lens does not authorize a target change or transaction.",),
    )
    if intelligence is None:
        evidence = SpecialistInterpretation(
            role="risk-cost-evidence",
            conclusion="wait_for_data",
            interpretation=(
                "Instrument look-through, historical metrics, and source freshness are "
                "unavailable, so an evidence-dependent policy conclusion is unsupported."
            ),
            evidence_references=(analysis.id,),
            limitations=("No structured research result was available.",),
        )
    else:
        all_stale = bool(intelligence.source_assessments) and all(
            source.freshness == "stale" for source in intelligence.source_assessments
        )
        missing_major_evidence = (
            intelligence.company_concentration.covered_portfolio_weight == 0
            or not intelligence.exposures
            or not intelligence.historical_metrics
        )
        if all_stale and missing_major_evidence:
            conclusion = "wait_for_data"
            interpretation = (
                "Research is stale and major look-through or historical evidence is "
                "missing; do not infer a target or thesis change from the gaps."
            )
        elif intelligence.company_concentration.unclassified_portfolio_weight > Decimal(
            "0.5"
        ):
            conclusion = "limited_evidence"
            interpretation = (
                "Look-through coverage is incomplete, so observed concentration is a "
                "lower-bound view and not a complete diversification conclusion."
            )
        else:
            conclusion = "monitor"
            interpretation = (
                "The supplied source coverage supports monitoring within the approved "
                "policy, subject to the listed data limitations."
            )
        evidence = SpecialistInterpretation(
            role="risk-cost-evidence",
            conclusion=conclusion,
            interpretation=interpretation,
            evidence_references=(intelligence.id, *intelligence.source_ids),
            limitations=intelligence.warnings,
        )
    return allocation, evidence


def _run_portfolio_review(
    request: CommitteeRequest,
    state: PortfolioState,
    prices: Sequence[MarketPrice],
    fx_rates: Sequence[FxRate],
    provider: ResearchProvider | None,
    stress_windows: Sequence[StressWindow],
) -> CommitteeResult:
    analysis = analyze_portfolio(state, prices, fx_rates, request.as_of)
    snapshot, provider_calls, provider_limitations = _fetch_research(
        request, state, provider
    )
    intelligence: PortfolioIntelligenceResult | None = None
    tools = ["analyze_portfolio"]
    if snapshot is not None:
        tools.extend(("ResearchProvider.fetch", "analyze_portfolio_intelligence"))
        intelligence = analyze_portfolio_intelligence(
            state, analysis, snapshot, request.as_of, stress_windows
        )
    lenses = _portfolio_lenses(analysis, intelligence)
    critic_passes = 1 if request.max_critic_passes == 1 else 0
    disagreements: tuple[str, ...] = ()
    if lenses[0].conclusion != lenses[1].conclusion:
        disagreements = (
            "The allocation lens supports policy-preserving drift correction, while "
            "the evidence lens limits or defers evidence-dependent conclusions.",
        )
    if critic_passes:
        lenses = (
            *lenses,
            SpecialistInterpretation(
                role="committee-critic",
                conclusion="preserve_boundary",
                interpretation=(
                    "Keep the policy-preserving drift fact separate from the "
                    "evidence-dependent conclusion; do not turn missing evidence into "
                    "a target change."
                ),
                evidence_references=tuple(
                    reference
                    for lens in lenses
                    for reference in lens.evidence_references
                ),
                limitations=("The critic adds no new source evidence.",),
            ),
        )

    facts = list(_analysis_facts(analysis))
    limitations = list(provider_limitations)
    sources = _market_sources(state, analysis.source_ids, request.as_of)
    status = "insufficient_evidence" if intelligence is None else "complete"
    if intelligence is not None:
        facts.extend(
            (
                "Observed company look-through covers "
                f"{_percent(intelligence.company_concentration.covered_portfolio_weight)} "
                "of portfolio weight.",
                "Unclassified company look-through is "
                f"{_percent(intelligence.company_concentration.unclassified_portfolio_weight)}.",
            )
        )
        limitations.extend(intelligence.warnings)
        sources = _combine_sources(sources, _research_sources(intelligence))
        all_stale = bool(intelligence.source_assessments) and all(
            source.freshness == "stale" for source in intelligence.source_assessments
        )
        missing_major_evidence = (
            intelligence.company_concentration.covered_portfolio_weight == 0
            or not intelligence.exposures
            or not intelligence.historical_metrics
        )
        if all_stale and missing_major_evidence:
            status = "insufficient_evidence"
        elif intelligence.warnings:
            status = "limited"

    synthesis = (
        "Use deterministic drift only within the approved policy; refresh missing or "
        "stale evidence before changing a target or thesis."
        if status == "insufficient_evidence"
        else "The portfolio can be reviewed against its approved policy, but partial "
        "look-through remains a limitation rather than evidence of zero exposure."
    )
    return CommitteeResult(
        id=f"committee:{request.id}:{request.as_of}",
        committee_version=COMMITTEE_VERSION,
        request_id=request.id,
        request_text=request.message,
        route="portfolio_review",
        status=status,
        as_of=request.as_of,
        deterministic_facts=tuple(facts),
        sources=sources,
        data_limitations=_unique(tuple(limitations)),
        assumptions=(
            "The approved target is the policy baseline.",
            "Missing research is unknown and is never treated as zero exposure.",
        ),
        specialist_interpretations=lenses,
        disagreements=disagreements,
        final_synthesis=synthesis,
        proposed_next_actions=(
            "Refresh missing or stale sources when the conclusion depends on them.",
            "Request explicit approval before persisting a target or policy change.",
        ),
        requires_user_approval=False,
        approval_reasons=(
            "A future target or policy change would require explicit user approval.",
        ),
        mutation_performed=False,
        trace=WorkflowTrace(
            route="portfolio_review",
            deterministic_tools=tuple(tools),
            review_lenses=tuple(item.role for item in lenses),
            provider_calls=provider_calls,
            external_calls=0,
            critic_passes=critic_passes,
            revisions=critic_passes,
            execution_mode=_EXECUTION_MODE,
        ),
    )


def _run_overlap_review(
    request: CommitteeRequest,
    state: PortfolioState,
    prices: Sequence[MarketPrice],
    fx_rates: Sequence[FxRate],
    provider: ResearchProvider | None,
) -> CommitteeResult:
    analysis = analyze_portfolio(state, prices, fx_rates, request.as_of)
    snapshot, provider_calls, provider_limitations = _fetch_research(
        request, state, provider
    )
    if snapshot is None:
        result = _run_portfolio_review(
            request, state, prices, fx_rates, None, ()
        )
        return replace(
            result,
            route="overlap_review",
            status="insufficient_evidence",
            data_limitations=provider_limitations,
            specialist_interpretations=(),
            disagreements=(),
            final_synthesis=(
                "Overlap cannot be assessed without a dated structured holdings snapshot."
            ),
            trace=WorkflowTrace(
                route="overlap_review",
                deterministic_tools=("analyze_portfolio",),
                review_lenses=(),
                provider_calls=provider_calls,
                external_calls=0,
                critic_passes=0,
                revisions=0,
                execution_mode=_EXECUTION_MODE,
            ),
        )
    intelligence = analyze_portfolio_intelligence(
        state, analysis, snapshot, request.as_of
    )
    facts = list(_analysis_facts(analysis))
    for overlap in intelligence.overlaps:
        facts.append(
            f"Observed overlap between {overlap.left_instrument_id} and "
            f"{overlap.right_instrument_id} is {_percent(overlap.observed_overlap_weight)}; "
            f"holdings coverage is {_percent(overlap.left_holdings_coverage)} and "
            f"{_percent(overlap.right_holdings_coverage)}."
        )
    no_overlap_evidence = not intelligence.overlaps
    partial = any(
        item.left_holdings_coverage < 1 or item.right_holdings_coverage < 1
        for item in intelligence.overlaps
    )
    lens = SpecialistInterpretation(
        role="allocation-diversification",
        conclusion="insufficient" if no_overlap_evidence else "partial_overlap",
        interpretation=(
            "No overlap conclusion is available from the supplied holdings."
            if no_overlap_evidence
            else "Observed overlap describes supplied holdings only; uncovered holdings "
            "could increase or decrease the complete-fund overlap."
        ),
        evidence_references=(intelligence.id, *intelligence.source_ids),
        limitations=intelligence.warnings,
    )
    evidence_lens = SpecialistInterpretation(
        role="evidence-quality",
        conclusion="refresh" if partial or no_overlap_evidence else "sufficient",
        interpretation=(
            "Refresh complete, same-date holdings before making a complete overlap claim."
            if partial or no_overlap_evidence
            else "The supplied holdings coverage is complete for this comparison."
        ),
        evidence_references=tuple(
            source.source_id for source in intelligence.source_assessments
        ),
        limitations=("Missing holdings are not treated as zero.",),
    )
    critic_passes = 1 if request.max_critic_passes == 1 and partial else 0
    lenses = (lens, evidence_lens)
    if critic_passes:
        lenses = (
            *lenses,
            SpecialistInterpretation(
                role="committee-critic",
                conclusion="reject_complete_overlap_claim",
                interpretation=(
                    "The observed overlap must not be presented as complete while "
                    "either holdings coverage value is below 100%."
                ),
                evidence_references=(intelligence.id,),
                limitations=("The critic adds no new holdings data.",),
            ),
        )
    return CommitteeResult(
        id=f"committee:{request.id}:{request.as_of}",
        committee_version=COMMITTEE_VERSION,
        request_id=request.id,
        request_text=request.message,
        route="overlap_review",
        status="insufficient_evidence" if no_overlap_evidence else "limited" if partial else "complete",
        as_of=request.as_of,
        deterministic_facts=tuple(facts),
        sources=_combine_sources(
            _market_sources(state, analysis.source_ids, request.as_of),
            _research_sources(intelligence),
        ),
        data_limitations=_unique((*provider_limitations, *intelligence.warnings)),
        assumptions=("Only supplied holdings contribute to observed overlap.",),
        specialist_interpretations=lenses,
        disagreements=(),
        final_synthesis=(
            "The observed overlap is useful as a covered-slice measurement, not as a "
            "complete-fund overlap estimate."
            if intelligence.overlaps
            else "Evidence is insufficient for an overlap conclusion."
        ),
        proposed_next_actions=(
            "Obtain complete, compatible, same-date holdings before a complete overlap conclusion.",
        ),
        requires_user_approval=False,
        approval_reasons=(),
        mutation_performed=False,
        trace=WorkflowTrace(
            route="overlap_review",
            deterministic_tools=(
                "analyze_portfolio",
                "ResearchProvider.fetch",
                "analyze_portfolio_intelligence",
            ),
            review_lenses=tuple(item.role for item in lenses),
            provider_calls=provider_calls,
            external_calls=0,
            critic_passes=critic_passes,
            revisions=critic_passes,
            execution_mode=_EXECUTION_MODE,
        ),
    )


def _resolve_thesis_id(request: CommitteeRequest, state: PortfolioState) -> str | None:
    if request.thesis_id is not None:
        return request.thesis_id
    matches = tuple(
        thesis.id
        for thesis in state.investment_theses
        if thesis.instrument_id == request.instrument_id and thesis.status == "active"
    )
    return matches[0] if len(matches) == 1 else None


def _run_thesis_review(
    request: CommitteeRequest,
    state: PortfolioState,
    provider: ResearchProvider | None,
    evidence: Sequence[ThesisEvidence],
    observed_review_triggers: Sequence[str],
) -> CommitteeResult:
    thesis_id = _resolve_thesis_id(request, state)
    if thesis_id is None:
        return _clarification_result(request, "thesis_review")
    snapshot, provider_calls, provider_limitations = _fetch_research(
        request, state, provider
    )
    if snapshot is None:
        return replace(
            _clarification_result(request, "thesis_review"),
            status="insufficient_evidence",
            data_limitations=provider_limitations,
            final_synthesis="Thesis review stopped because sourced evidence is unavailable.",
            trace=WorkflowTrace(
                route="thesis_review",
                deterministic_tools=(),
                review_lenses=(),
                provider_calls=provider_calls,
                external_calls=0,
                critic_passes=0,
                revisions=0,
                execution_mode=_EXECUTION_MODE,
            ),
        )
    review = review_investment_thesis(
        state,
        thesis_id,
        evidence,
        observed_review_triggers,
        request.as_of,
        snapshot,
    )
    fit_lens = SpecialistInterpretation(
        role="thesis-fit",
        conclusion=review.proposed_action,
        interpretation=(
            f"The deterministic thesis review proposes {review.proposed_action}; "
            "price movement alone is not treated as thesis failure."
        ),
        evidence_references=(review.id, *review.source_ids),
        limitations=review.limitations,
    )
    all_stale = bool(review.source_assessments) and all(
        item.freshness == "stale" for item in review.source_assessments
    )
    evidence_conclusion = "wait_for_data" if not evidence or all_stale else "usable_with_limits"
    evidence_lens = SpecialistInterpretation(
        role="evidence-quality",
        conclusion=evidence_conclusion,
        interpretation=(
            "Evidence is absent or stale, so retention or removal should not be concluded."
            if evidence_conclusion == "wait_for_data"
            else "The dated evidence can inform review within its explicit limitations."
        ),
        evidence_references=tuple(item.id for item in evidence),
        limitations=review.limitations,
    )
    disagreements = ()
    if evidence_conclusion == "wait_for_data" and review.proposed_action != "investigate":
        disagreements = (
            f"The thesis-fit lens proposes {review.proposed_action}, while the evidence-quality "
            "lens says the available evidence is not current enough for that conclusion.",
        )
    critic_passes = 1 if request.max_critic_passes == 1 and disagreements else 0
    lenses = (fit_lens, evidence_lens)
    if critic_passes:
        lenses = (
            *lenses,
            SpecialistInterpretation(
                role="committee-critic",
                conclusion="defer_conclusion",
                interpretation=(
                    "Source quality governs the conclusion: preserve the thesis state "
                    "and collect current evidence instead of forcing agreement."
                ),
                evidence_references=(review.id,),
                limitations=("The critic adds no new source evidence.",),
            ),
        )
    status = "insufficient_evidence" if evidence_conclusion == "wait_for_data" else "complete"
    if status == "complete" and any(
        item.freshness == "stale" for item in review.source_assessments
    ):
        status = "limited"
    facts = (
        f"Thesis {review.thesis_id} has role {review.role} and deterministic proposed action {review.proposed_action}.",
        f"Target weight is {_percent(review.target_weight)}."
        if review.target_weight is not None
        else "The thesis has no target weight.",
        f"Evidence facts supplied: {len(review.evidence_facts)}; triggered review conditions: {len(review.triggered_review_conditions)}.",
    )
    approval_reasons = (
        "Persisting a target or policy change requires explicit user approval.",
    ) if review.proposed_action == "review" else ()
    return CommitteeResult(
        id=f"committee:{request.id}:{request.as_of}",
        committee_version=COMMITTEE_VERSION,
        request_id=request.id,
        request_text=request.message,
        route="thesis_review",
        status=status,
        as_of=request.as_of,
        deterministic_facts=facts,
        sources=_research_sources(review),
        data_limitations=_unique((*provider_limitations, *review.limitations)),
        assumptions=(
            "The active thesis and approved target remain unchanged unless separately approved.",
        ),
        specialist_interpretations=lenses,
        disagreements=disagreements,
        final_synthesis=(
            "Stop at evidence collection; do not manufacture consensus or change policy."
            if status == "insufficient_evidence"
            else f"The bounded review supports the deterministic {review.proposed_action} proposal, "
            "subject to source dates and limitations."
        ),
        proposed_next_actions=review.proposed_changes,
        requires_user_approval=bool(approval_reasons),
        approval_reasons=approval_reasons,
        mutation_performed=False,
        trace=WorkflowTrace(
            route="thesis_review",
            deterministic_tools=("ResearchProvider.fetch", "review_investment_thesis"),
            review_lenses=tuple(item.role for item in lenses),
            provider_calls=provider_calls,
            external_calls=0,
            critic_passes=critic_passes,
            revisions=critic_passes,
            execution_mode=_EXECUTION_MODE,
        ),
    )


def run_committee_workflow(
    request: CommitteeRequest,
    state: PortfolioState,
    prices: Sequence[MarketPrice] = (),
    fx_rates: Sequence[FxRate] = (),
    constraints: Sequence[TradingConstraint] = (),
    *,
    preferred_listings: Mapping[str, str] | None = None,
    research_provider: ResearchProvider | None = None,
    stress_windows: Sequence[StressWindow] = (),
    thesis_evidence: Sequence[ThesisEvidence] = (),
    observed_review_triggers: Sequence[str] = (),
) -> CommitteeResult:
    """Run one bounded workflow and return an explanation-ready structured result."""

    route = route_request(request)
    if route == "contribution":
        return _run_contribution(
            request,
            state,
            prices,
            fx_rates,
            constraints,
            preferred_listings,
        )
    if route == "portfolio_review":
        return _run_portfolio_review(
            request,
            state,
            prices,
            fx_rates,
            research_provider,
            stress_windows,
        )
    if route == "overlap_review":
        return _run_overlap_review(
            request, state, prices, fx_rates, research_provider
        )
    if route == "thesis_review":
        return _run_thesis_review(
            request,
            state,
            research_provider,
            thesis_evidence,
            observed_review_triggers,
        )
    return _clarification_result(request, route)
