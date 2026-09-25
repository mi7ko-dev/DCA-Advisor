"""Deterministic portfolio intelligence over structured provider snapshots."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal, localcontext
from itertools import combinations
from typing import Sequence

from .errors import ValidationError
from .models import AnalysisResult, InvestmentThesis, PortfolioState
from .research_models import (
    INTELLIGENCE_CALCULATION_VERSION,
    CompanyConcentration,
    CompanyExposure,
    CorrelationMetric,
    ExposureAnalysis,
    ExposureEntry,
    HistoricalMetric,
    HistoricalSeries,
    InstrumentResearchSummary,
    ListingIdentity,
    OverlapResult,
    PortfolioIntelligenceResult,
    ResearchSnapshot,
    SourceAssessment,
    StressMetric,
    StressWindow,
)
from .research_validation import validate_research_snapshot
from .validation import validate_state


_WEIGHT_TOLERANCE = Decimal("0.00000001")
_PERIODS_PER_YEAR = {"daily": Decimal("252"), "weekly": Decimal("52"), "monthly": Decimal("12")}


def _as_date(value: str, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValidationError(f"{field} must be an ISO date.") from error


def _unique(items: Sequence[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(items))


def _validate_references(
    state: PortfolioState, snapshot: ResearchSnapshot, analysis_date: date
) -> None:
    instruments = {instrument.id: instrument for instrument in state.instruments}
    listings = {listing.id: listing for listing in state.listings}
    sources = {source.id: source for source in snapshot.sources}

    for source in snapshot.sources:
        if _as_date(source.as_of, "sources[].as_of") > analysis_date:
            raise ValidationError("Research source data cannot be newer than the analysis date.")
    for fund in snapshot.funds:
        instrument = instruments.get(fund.instrument_id)
        if instrument is None:
            raise ValidationError("A fund profile references an unknown instrument.")
        if instrument.kind != "etf":
            raise ValidationError("Fund profiles may reference ETF instruments only.")
    for holding in snapshot.fund_holdings:
        instrument = instruments.get(holding.fund_instrument_id)
        if instrument is None or instrument.kind != "etf":
            raise ValidationError("A fund holding references an unknown ETF instrument.")
    for exposure in snapshot.classified_exposures:
        if exposure.instrument_id not in instruments:
            raise ValidationError("A classified exposure references an unknown instrument.")
    for series in snapshot.historical_series:
        if series.listing_id not in listings:
            raise ValidationError("A historical series references an unknown listing.")
        if series.source_id not in sources:
            raise ValidationError("A historical series references an unknown source.")


def _validate_analysis(state: PortfolioState, analysis: AnalysisResult, analysis_date: str) -> None:
    if analysis.valuation_date != analysis_date:
        raise ValidationError("Portfolio and intelligence analysis dates must match.")
    if analysis.base_currency != state.investor_profile.base_currency:
        raise ValidationError("Portfolio analysis uses an inconsistent base currency.")
    known = {instrument.id for instrument in state.instruments}
    if len({position.instrument_id for position in analysis.positions}) != len(analysis.positions):
        raise ValidationError("Portfolio analysis contains duplicate instruments.")
    if any(position.instrument_id not in known for position in analysis.positions):
        raise ValidationError("Portfolio analysis references an unknown instrument.")
    if not analysis.total_value.is_finite() or analysis.total_value < 0 or any(
        not position.current_value.is_finite()
        or not position.current_weight.is_finite()
        or not position.target_weight.is_finite()
        or not position.drift.is_finite()
        or position.current_value < 0
        or position.current_weight < 0
        for position in analysis.positions
    ):
        raise ValidationError("Portfolio analysis contains negative values or weights.")
    approved = next(
        allocation
        for allocation in state.target_allocations
        if allocation.status == "approved"
    )
    target_weights = {
        target.instrument_id: target.weight for target in approved.targets
    }
    listing_instruments = {
        listing.id: listing.instrument_id for listing in state.listings
    }
    expected_ids = set(target_weights)
    expected_ids.update(
        listing_instruments[holding.listing_id]
        for holding in state.holdings
        if holding.quantity > 0
    )
    if {position.instrument_id for position in analysis.positions} != expected_ids:
        raise ValidationError("Portfolio analysis does not match held and targeted instruments.")
    if sum(
        (position.current_value for position in analysis.positions), Decimal("0")
    ) != analysis.total_value:
        raise ValidationError("Portfolio analysis total does not match position values.")
    for position in analysis.positions:
        expected_target = target_weights.get(position.instrument_id, Decimal("0"))
        if position.target_weight != expected_target:
            raise ValidationError("Portfolio analysis target weights are stale or modified.")
        if position.drift != position.current_weight - position.target_weight:
            raise ValidationError("Portfolio analysis drift is stale or modified.")
    if analysis.total_value > 0:
        weight_total = sum(
            (position.current_weight for position in analysis.positions), Decimal("0")
        )
        if abs(weight_total - Decimal("1")) > _WEIGHT_TOLERANCE:
            raise ValidationError("Portfolio analysis weights must sum to one.")
        for position in analysis.positions:
            expected = position.current_value / analysis.total_value
            if abs(expected - position.current_weight) > _WEIGHT_TOLERANCE:
                raise ValidationError("Portfolio analysis weights do not match values.")
    elif any(position.current_weight != 0 for position in analysis.positions):
        raise ValidationError("A zero-value portfolio must have zero current weights.")


def _instrument_summaries(
    state: PortfolioState,
    active_ids: Sequence[str],
    snapshot: ResearchSnapshot,
    used_sources: set[str],
    warnings: list[str],
) -> tuple[InstrumentResearchSummary, ...]:
    instruments = {instrument.id: instrument for instrument in state.instruments}
    profiles = {profile.instrument_id: profile for profile in snapshot.funds}
    sources = {source.id: source for source in snapshot.sources}
    listings_by_instrument: dict[str, list[ListingIdentity]] = defaultdict(list)
    for listing in state.listings:
        listings_by_instrument[listing.instrument_id].append(
            ListingIdentity(
                listing_id=listing.id,
                mic=listing.mic,
                ticker=listing.ticker,
                trading_currency=listing.trading_currency,
            )
        )

    result: list[InstrumentResearchSummary] = []
    for instrument_id in active_ids:
        instrument = instruments[instrument_id]
        profile = profiles.get(instrument_id)
        limitations: list[str] = []
        if instrument.kind == "etf" and profile is None:
            limitations.append("No structured fund profile was supplied.")
            warnings.append(f"Fund metadata is unavailable for {instrument_id}.")
        if profile is not None:
            source = sources[profile.source_id]
            used_sources.add(profile.source_id)
            limitations.extend(source.limitations)
            if profile.ter is not None and profile.ter != instrument.annual_fee_rate:
                limitations.append(
                    "Provider TER differs from the portfolio record; neither value was overwritten."
                )
                warnings.append(f"TER differs between source and portfolio for {instrument_id}.")
        result.append(
            InstrumentResearchSummary(
                instrument_id=instrument.id,
                name=instrument.name,
                kind=instrument.kind,
                isin=instrument.isin,
                economic_currency=instrument.economic_currency,
                listings=tuple(
                    sorted(
                        listings_by_instrument.get(instrument_id, []),
                        key=lambda item: item.listing_id,
                    )
                ),
                domicile=profile.domicile if profile else None,
                distribution_policy=profile.distribution_policy if profile else None,
                index_name=profile.index_name if profile else None,
                replication_method=profile.replication_method if profile else None,
                ter=profile.ter if profile else None,
                fund_size=profile.fund_size if profile else None,
                fund_size_currency=profile.fund_size_currency if profile else None,
                facts_as_of=profile.as_of if profile else None,
                source_id=profile.source_id if profile else None,
                limitations=_unique(limitations),
            )
        )
    return tuple(result)


def _overlap(
    state: PortfolioState,
    active_ids: Sequence[str],
    snapshot: ResearchSnapshot,
    used_sources: set[str],
) -> tuple[OverlapResult, ...]:
    instruments = {instrument.id: instrument for instrument in state.instruments}
    etf_ids = [item for item in active_ids if instruments[item].kind == "etf"]
    holdings: dict[str, dict[str, object]] = defaultdict(dict)
    for holding in snapshot.fund_holdings:
        holdings[holding.fund_instrument_id][holding.constituent_id] = holding
    sources = {source.id: source for source in snapshot.sources}

    result: list[OverlapResult] = []
    for left_id, right_id in combinations(etf_ids, 2):
        left = holdings.get(left_id, {})
        right = holdings.get(right_id, {})
        left_coverage = sum(
            (item.weight for item in left.values()), Decimal("0")  # type: ignore[attr-defined]
        )
        right_coverage = sum(
            (item.weight for item in right.values()), Decimal("0")  # type: ignore[attr-defined]
        )
        observed = sum(
            (
                min(left[key].weight, right[key].weight)  # type: ignore[attr-defined]
                for key in set(left) & set(right)
            ),
            Decimal("0"),
        )
        rows = tuple(left.values()) + tuple(right.values())
        source_ids = tuple(sorted({item.source_id for item in rows}))  # type: ignore[attr-defined]
        used_sources.update(source_ids)
        source_limitations = [
            limitation
            for source_id in source_ids
            for limitation in sources[source_id].limitations
        ]
        limitations = _unique(
            [
                "Observed overlap uses supplied holdings only; missing holdings are not zero exposure.",
                *source_limitations,
            ]
        )
        result.append(
            OverlapResult(
                left_instrument_id=left_id,
                right_instrument_id=right_id,
                observed_overlap_weight=observed,
                left_holdings_coverage=left_coverage,
                right_holdings_coverage=right_coverage,
                holdings_as_of_dates=tuple(sorted({item.as_of for item in rows})),  # type: ignore[attr-defined]
                source_ids=source_ids,
                limitations=limitations,
            )
        )
    return tuple(result)


def _company_concentration(
    state: PortfolioState,
    analysis: AnalysisResult,
    snapshot: ResearchSnapshot,
    used_sources: set[str],
) -> CompanyConcentration:
    instruments = {instrument.id: instrument for instrument in state.instruments}
    holdings: dict[str, list[object]] = defaultdict(list)
    for holding in snapshot.fund_holdings:
        holdings[holding.fund_instrument_id].append(holding)
    sources = {source.id: source for source in snapshot.sources}
    weights: dict[tuple[str, str], Decimal] = defaultdict(lambda: Decimal("0"))
    covered = Decimal("0")
    total_weight = Decimal("0")
    dates: set[str] = set()
    source_ids: set[str] = set()

    for position in analysis.positions:
        if position.current_weight <= 0:
            continue
        total_weight += position.current_weight
        instrument = instruments[position.instrument_id]
        if instrument.kind == "stock":
            weights[(instrument.id, instrument.name)] += position.current_weight
            covered += position.current_weight
            continue
        rows = holdings.get(instrument.id, [])
        fund_coverage = sum((row.weight for row in rows), Decimal("0"))  # type: ignore[attr-defined]
        covered += position.current_weight * fund_coverage
        for row in rows:
            weights[(row.constituent_id, row.constituent_name)] += (  # type: ignore[attr-defined]
                position.current_weight * row.weight  # type: ignore[attr-defined]
            )
            dates.add(row.as_of)  # type: ignore[attr-defined]
            source_ids.add(row.source_id)  # type: ignore[attr-defined]

    used_sources.update(source_ids)
    exposures = tuple(
        CompanyExposure(
            constituent_id=key[0],
            name=key[1],
            observed_portfolio_weight=value,
        )
        for key, value in sorted(weights.items(), key=lambda item: (-item[1], item[0]))
    )
    source_limitations = [
        limitation
        for source_id in sorted(source_ids)
        for limitation in sources[source_id].limitations
    ]
    return CompanyConcentration(
        exposures=exposures,
        covered_portfolio_weight=covered,
        unclassified_portfolio_weight=max(Decimal("0"), total_weight - covered),
        maximum_observed_company_weight=max(
            (item.observed_portfolio_weight for item in exposures),
            default=Decimal("0"),
        ),
        holdings_as_of_dates=tuple(sorted(dates)),
        source_ids=tuple(sorted(source_ids)),
        limitations=_unique(
            [
                "Company concentration is observed look-through coverage, not a complete portfolio exposure map.",
                "Unclassified portfolio weight is reported explicitly and is not treated as zero exposure.",
                *source_limitations,
            ]
        ),
    )


def _exposures(
    analysis: AnalysisResult,
    snapshot: ResearchSnapshot,
    used_sources: set[str],
    warnings: list[str],
) -> tuple[ExposureAnalysis, ...]:
    rows: dict[tuple[str, str], list[object]] = defaultdict(list)
    for exposure in snapshot.classified_exposures:
        rows[(exposure.instrument_id, exposure.dimension)].append(exposure)
    sources = {source.id: source for source in snapshot.sources}
    positive_positions = [
        position for position in analysis.positions if position.current_weight > 0
    ]
    total_weight = sum(
        (position.current_weight for position in positive_positions), Decimal("0")
    )
    result: list[ExposureAnalysis] = []

    for dimension in ("sector", "geography", "currency"):
        if not any(rows.get((position.instrument_id, dimension)) for position in positive_positions):
            warnings.append(
                f"{dimension.capitalize()} exposure is unavailable; missing data was not treated as zero."
            )
            continue
        aggregate: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        covered = Decimal("0")
        dates: set[str] = set()
        source_ids: set[str] = set()
        for position in positive_positions:
            instrument_rows = rows.get((position.instrument_id, dimension), [])
            instrument_coverage = sum(
                (row.weight for row in instrument_rows), Decimal("0")  # type: ignore[attr-defined]
            )
            covered += position.current_weight * instrument_coverage
            for row in instrument_rows:
                aggregate[row.label] += position.current_weight * row.weight  # type: ignore[attr-defined]
                dates.add(row.as_of)  # type: ignore[attr-defined]
                source_ids.add(row.source_id)  # type: ignore[attr-defined]
        used_sources.update(source_ids)
        source_limitations = [
            limitation
            for source_id in sorted(source_ids)
            for limitation in sources[source_id].limitations
        ]
        result.append(
            ExposureAnalysis(
                dimension=dimension,
                entries=tuple(
                    ExposureEntry(label=label, observed_portfolio_weight=weight)
                    for label, weight in sorted(
                        aggregate.items(), key=lambda item: (-item[1], item[0])
                    )
                ),
                covered_portfolio_weight=covered,
                unclassified_portfolio_weight=max(
                    Decimal("0"), total_weight - covered
                ),
                as_of_dates=tuple(sorted(dates)),
                source_ids=tuple(sorted(source_ids)),
                methodologies=tuple(
                    sorted({sources[source_id].methodology for source_id in source_ids})
                ),
                limitations=_unique(
                    [
                        "Exposure totals use supplied classifications only; unclassified weight remains explicit.",
                        *source_limitations,
                    ]
                ),
            )
        )
    return tuple(result)


def _returns(series: HistoricalSeries) -> tuple[Decimal, ...]:
    return tuple(
        current.value / previous.value - Decimal("1")
        for previous, current in zip(series.observations, series.observations[1:])
    )


def _cumulative_return(series: HistoricalSeries) -> Decimal:
    return series.observations[-1].value / series.observations[0].value - Decimal("1")


def _annualized_volatility(series: HistoricalSeries) -> Decimal:
    values = _returns(series)
    if len(values) < 2:
        return Decimal("0")
    mean = sum(values, Decimal("0")) / Decimal(len(values))
    variance = sum(((item - mean) ** 2 for item in values), Decimal("0")) / Decimal(
        len(values) - 1
    )
    return variance.sqrt() * _PERIODS_PER_YEAR[series.frequency].sqrt()


def _maximum_drawdown(series: HistoricalSeries) -> Decimal:
    peak = series.observations[0].value
    maximum = Decimal("0")
    for observation in series.observations:
        peak = max(peak, observation.value)
        maximum = max(maximum, (peak - observation.value) / peak)
    return maximum


def _compatible(left: HistoricalSeries, right: HistoricalSeries) -> bool:
    return (
        tuple(item.date for item in left.observations)
        == tuple(item.date for item in right.observations)
        and left.currency == right.currency
        and left.frequency == right.frequency
        and left.return_convention == right.return_convention
        and left.distribution_treatment == right.distribution_treatment
        and left.corporate_action_treatment == right.corporate_action_treatment
    )


def _correlation(left: HistoricalSeries, right: HistoricalSeries) -> Decimal | None:
    left_returns = _returns(left)
    right_returns = _returns(right)
    if len(left_returns) < 2:
        return None
    left_mean = sum(left_returns, Decimal("0")) / Decimal(len(left_returns))
    right_mean = sum(right_returns, Decimal("0")) / Decimal(len(right_returns))
    covariance = sum(
        (
            (left_item - left_mean) * (right_item - right_mean)
            for left_item, right_item in zip(left_returns, right_returns)
        ),
        Decimal("0"),
    )
    left_squares = sum(
        ((item - left_mean) ** 2 for item in left_returns), Decimal("0")
    )
    right_squares = sum(
        ((item - right_mean) ** 2 for item in right_returns), Decimal("0")
    )
    denominator = (left_squares * right_squares).sqrt()
    if denominator == 0:
        return None
    return covariance / denominator


def _select_series(
    instrument_id: str,
    state: PortfolioState,
    series_by_listing: dict[str, HistoricalSeries],
) -> HistoricalSeries | None:
    listing_ids = {
        listing.id for listing in state.listings if listing.instrument_id == instrument_id
    }
    candidates = [series_by_listing[item] for item in listing_ids if item in series_by_listing]
    if len(candidates) > 1:
        held_listing_ids = {
            holding.listing_id
            for holding in state.holdings
            if holding.listing_id in listing_ids and holding.quantity > 0
        }
        held_candidates = [item for item in candidates if item.listing_id in held_listing_ids]
        if len(held_candidates) == 1:
            return held_candidates[0]
        raise ValidationError(
            "Historical analysis needs one unambiguous listing series per instrument."
        )
    return candidates[0] if candidates else None


def _historical_analysis(
    state: PortfolioState,
    analysis: AnalysisResult,
    snapshot: ResearchSnapshot,
    stress_windows: Sequence[StressWindow],
    used_sources: set[str],
    warnings: list[str],
) -> tuple[
    tuple[HistoricalMetric, ...],
    tuple[CorrelationMetric, ...],
    tuple[StressMetric, ...],
]:
    series_by_listing = {series.listing_id: series for series in snapshot.historical_series}
    active_positions = [
        position
        for position in analysis.positions
        if position.current_weight > 0 or position.target_weight > 0
    ]
    selected: dict[str, HistoricalSeries] = {}
    for position in active_positions:
        series = _select_series(position.instrument_id, state, series_by_listing)
        if series is None:
            warnings.append(f"Historical data is unavailable for {position.instrument_id}.")
            continue
        if series.currency != analysis.base_currency:
            raise ValidationError(
                "Historical series must use the portfolio base currency in the MVP."
            )
        selected[position.instrument_id] = series

    selected_values = tuple(selected.values())
    for left, right in combinations(selected_values, 2):
        if not _compatible(left, right):
            raise ValidationError(
                "Historical series must use compatible dates, currencies, frequencies, return conventions, and treatments."
            )

    theses: dict[str, InvestmentThesis] = {
        thesis.instrument_id: thesis
        for thesis in state.investment_theses
        if thesis.status == "active"
    }
    metrics: list[HistoricalMetric] = []
    for instrument_id, series in selected.items():
        used_sources.add(series.source_id)
        thesis = theses.get(instrument_id)
        benchmark_series: HistoricalSeries | None = None
        benchmark_listing_id: str | None = None
        limitations = [
            "Historical metrics describe the supplied period and are not predictions."
        ]
        if series.return_convention == "price_index":
            limitations.append("Price-index returns exclude distributions.")
        if thesis is None or thesis.benchmark_instrument_id is None:
            limitations.append("No benchmark is configured for this holding thesis.")
        else:
            benchmark_series = _select_series(
                thesis.benchmark_instrument_id, state, series_by_listing
            )
            if benchmark_series is None:
                limitations.append("The configured benchmark has no historical series.")
                warnings.append(f"Benchmark data is unavailable for {instrument_id}.")
            elif not _compatible(series, benchmark_series):
                raise ValidationError(
                    "A benchmark series must use the same period, currency, frequency, return convention, and treatments."
                )
            else:
                benchmark_listing_id = benchmark_series.listing_id
                used_sources.add(benchmark_series.source_id)
        benchmark_return = (
            _cumulative_return(benchmark_series) if benchmark_series else None
        )
        cumulative = _cumulative_return(series)
        metrics.append(
            HistoricalMetric(
                instrument_id=instrument_id,
                listing_id=series.listing_id,
                start_date=series.observations[0].date,
                end_date=series.observations[-1].date,
                observation_count=len(series.observations),
                currency=series.currency,
                frequency=series.frequency,
                return_convention=series.return_convention,
                distribution_treatment=series.distribution_treatment,
                corporate_action_treatment=series.corporate_action_treatment,
                cumulative_return=cumulative,
                annualized_volatility=_annualized_volatility(series),
                maximum_drawdown=_maximum_drawdown(series),
                benchmark_listing_id=benchmark_listing_id,
                benchmark_cumulative_return=benchmark_return,
                excess_return=(
                    cumulative - benchmark_return
                    if benchmark_return is not None
                    else None
                ),
                source_ids=tuple(
                    sorted(
                        {
                            series.source_id,
                            *(
                                (benchmark_series.source_id,)
                                if benchmark_series is not None
                                else ()
                            ),
                        }
                    )
                ),
                limitations=tuple(limitations),
            )
        )

    correlations: list[CorrelationMetric] = []
    for (left_id, left), (right_id, right) in combinations(selected.items(), 2):
        correlation = _correlation(left, right)
        if correlation is None:
            warnings.append(
                f"Correlation is undefined for {left_id} and {right_id}."
            )
            continue
        correlations.append(
            CorrelationMetric(
                left_instrument_id=left_id,
                right_instrument_id=right_id,
                start_date=left.observations[0].date,
                end_date=left.observations[-1].date,
                return_observation_count=len(left.observations) - 1,
                correlation=correlation,
                source_ids=tuple(sorted({left.source_id, right.source_id})),
            )
        )

    stress_metrics: list[StressMetric] = []
    for window in stress_windows:
        start = _as_date(window.start_date, "stress_windows[].start_date")
        end = _as_date(window.end_date, "stress_windows[].end_date")
        if start >= end:
            raise ValidationError("A stress window must end after it starts.")
        for instrument_id, series in selected.items():
            observations = tuple(
                item
                for item in series.observations
                if start <= _as_date(item.date, "historical observation date") <= end
            )
            if len(observations) < 2:
                warnings.append(
                    f"Stress window {window.id} has insufficient data for {instrument_id}."
                )
                continue
            subset = HistoricalSeries(
                listing_id=series.listing_id,
                currency=series.currency,
                frequency=series.frequency,
                return_convention=series.return_convention,
                distribution_treatment=series.distribution_treatment,
                corporate_action_treatment=series.corporate_action_treatment,
                observations=observations,
                as_of=observations[-1].date,
                source_id=series.source_id,
            )
            limitations: list[str] = []
            if observations[0].date != window.start_date or observations[-1].date != window.end_date:
                limitations.append(
                    "The metric uses available observations inside the requested stress window."
                )
            stress_metrics.append(
                StressMetric(
                    stress_id=window.id,
                    stress_name=window.name,
                    instrument_id=instrument_id,
                    listing_id=series.listing_id,
                    start_date=observations[0].date,
                    end_date=observations[-1].date,
                    observation_count=len(observations),
                    cumulative_return=_cumulative_return(subset),
                    maximum_drawdown=_maximum_drawdown(subset),
                    source_id=series.source_id,
                    limitations=tuple(limitations),
                )
            )
    return tuple(metrics), tuple(correlations), tuple(stress_metrics)


def analyze_portfolio_intelligence(
    state: PortfolioState,
    analysis: AnalysisResult,
    snapshot: ResearchSnapshot,
    analysis_date: str,
    stress_windows: Sequence[StressWindow] = (),
) -> PortfolioIntelligenceResult:
    """Combine portfolio weights with explicit, coverage-aware research data."""

    validate_state(state)
    validate_research_snapshot(snapshot)
    _validate_analysis(state, analysis, analysis_date)
    parsed_date = _as_date(analysis_date, "analysis_date")
    _validate_references(state, snapshot, parsed_date)
    if len({window.id for window in stress_windows}) != len(stress_windows):
        raise ValidationError("Stress window identifiers must be unique.")
    if any(
        _as_date(window.end_date, "stress_windows[].end_date") > parsed_date
        for window in stress_windows
    ):
        raise ValidationError("A stress window cannot end after the analysis date.")

    active_ids = tuple(
        position.instrument_id
        for position in analysis.positions
        if position.current_weight > 0 or position.target_weight > 0
    )
    used_sources: set[str] = set()
    warnings: list[str] = []

    with localcontext() as context:
        context.prec = 36
        summaries = _instrument_summaries(
            state, active_ids, snapshot, used_sources, warnings
        )
        overlaps = _overlap(state, active_ids, snapshot, used_sources)
        concentration = _company_concentration(
            state, analysis, snapshot, used_sources
        )
        exposures = _exposures(analysis, snapshot, used_sources, warnings)
        historical, correlations, stress = _historical_analysis(
            state,
            analysis,
            snapshot,
            stress_windows,
            used_sources,
            warnings,
        )

    source_by_id = {source.id: source for source in snapshot.sources}
    assessments: list[SourceAssessment] = []
    for source_id in sorted(used_sources):
        source = source_by_id[source_id]
        age = (parsed_date - _as_date(source.as_of, "sources[].as_of")).days
        freshness = "fresh" if age <= source.freshness_days else "stale"
        if freshness == "stale":
            warnings.append(
                f"Research source {source.id} is stale at {age} days old."
            )
        assessments.append(
            SourceAssessment(
                source_id=source.id,
                provider=source.provider,
                reference=source.reference,
                as_of=source.as_of,
                retrieved_at=source.retrieved_at,
                age_days=age,
                freshness=freshness,
                methodology=source.methodology,
                limitations=source.limitations,
                terms_reference=source.terms_reference,
                cache_permitted=source.cache_permitted,
                redistribution_permitted=source.redistribution_permitted,
            )
        )

    if concentration.unclassified_portfolio_weight > 0:
        warnings.append(
            "Company concentration is partial; unclassified portfolio weight is not zero exposure."
        )
    for exposure in exposures:
        if exposure.unclassified_portfolio_weight > 0:
            warnings.append(
                f"{exposure.dimension.capitalize()} exposure is partial; unclassified weight remains."
            )

    return PortfolioIntelligenceResult(
        id=f"intelligence:{state.investor_profile.id}:{analysis_date}",
        calculation_version=INTELLIGENCE_CALCULATION_VERSION,
        analysis_date=analysis_date,
        base_currency=analysis.base_currency,
        instrument_summaries=summaries,
        overlaps=overlaps,
        company_concentration=concentration,
        exposures=exposures,
        historical_metrics=historical,
        correlations=correlations,
        stress_metrics=stress,
        source_assessments=tuple(assessments),
        source_ids=tuple(sorted(used_sources)),
        warnings=_unique(warnings),
    )
