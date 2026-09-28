"""Deterministic equity-review and configurable portfolio-policy tests."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
import json
from pathlib import Path
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from steadyfolio.equity import review_equity  # noqa: E402
from steadyfolio.equity_models import (  # noqa: E402
    BooleanEvidence,
    CircleOfCompetenceEvidence,
    DecimalEvidence,
    EquityQualityEvidence,
    EquityReviewInput,
    FreeCashFlowObservation,
    InstrumentIdentityEvidence,
    OwnerEarningsEvidence,
    ValuationAnchor,
)
from steadyfolio.equity_validation import equity_review_input_from_dict  # noqa: E402
from steadyfolio.errors import ValidationError  # noqa: E402
from steadyfolio.models import Instrument, Listing, to_json_value  # noqa: E402
from steadyfolio.portfolio_policy import (  # noqa: E402
    FactorGroupPolicy,
    PortfolioPolicy,
    evaluate_portfolio_policy,
    portfolio_policy_from_dict,
)
from steadyfolio.research_models import ResearchSource  # noqa: E402
from steadyfolio.storage import (  # noqa: E402
    save_equity_review,
    save_portfolio_policy_result,
)
from steadyfolio.validation import (  # noqa: E402
    fx_rates_from_dict,
    market_prices_from_dict,
    state_from_dict,
    validate_state,
)
from steadyfolio.calculations import analyze_portfolio  # noqa: E402


EXAMPLES = REPOSITORY_ROOT / "examples"
REVIEW_DATE = "2026-01-31"


def _read(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _stock_state():
    state = state_from_dict(_read(EXAMPLES / "portfolio.example.json"))
    stock = replace(
        state.instruments[0],
        kind="stock",
        name="Synthetic Compute Company",
        isin="IE00SYNTH035",
        annual_fee_rate=Decimal("0"),
    )
    return replace(state, instruments=(stock, *state.instruments[1:]))


def _source(source_id: str = "synthetic-equity-source") -> ResearchSource:
    return ResearchSource(
        id=source_id,
        provider="Synthetic Equity Research Provider",
        reference=f"synthetic://{source_id}",
        as_of=REVIEW_DATE,
        retrieved_at="2026-01-31T18:00:00+00:00",
        methodology="Synthetic values for deterministic tests only.",
        limitations=("Not live market data.",),
        freshness_days=7,
        terms_reference="synthetic://terms",
        cache_permitted=True,
        redistribution_permitted=True,
    )


def _decimal(value: str, source_id: str = "synthetic-equity-source") -> DecimalEvidence:
    return DecimalEvidence(
        value=Decimal(value),
        as_of=REVIEW_DATE,
        source_id=source_id,
    )


def _boolean(
    value: bool,
    rationale: str,
    source_id: str = "synthetic-equity-source",
) -> BooleanEvidence:
    return BooleanEvidence(
        value=value,
        rationale=rationale,
        as_of=REVIEW_DATE,
        source_id=source_id,
    )


def _review_input(**changes) -> EquityReviewInput:
    source = _source()
    base = EquityReviewInput(
        schema_version="1.0",
        as_of=REVIEW_DATE,
        identity=InstrumentIdentityEvidence(
            instrument_id="instrument-global",
            reported_name="Synthetic Compute Company",
            isin="IE00SYNTH035",
            source_id=source.id,
            listing_id="listing-global-xetr",
            mic="XETR",
            ticker="WLDX",
            trading_currency="EUR",
        ),
        circle_of_competence=CircleOfCompetenceEvidence(
            business_model_understood=True,
            business_model_summary="Sells synthetic compute capacity to diversified customers.",
            revenue_drivers_understood=True,
            revenue_driver_summary="Revenue changes with contracted capacity and utilization.",
            external_dependency=None,
            observable_event=None,
        ),
        quality=EquityQualityEvidence(
            free_cash_flow=(
                FreeCashFlowObservation("2023-12-31", Decimal("100"), source.id),
                FreeCashFlowObservation("2024-12-31", Decimal("120"), source.id),
                FreeCashFlowObservation("2025-12-31", Decimal("140"), source.id),
            ),
            debt_to_ebitda=_decimal("1.5"),
            revenue_growth=_decimal("0.12"),
            operating_margin=_decimal("0.20"),
            capex_to_revenue=_decimal("0.10"),
            institutional_ownership=_decimal("0.60"),
            benchmark_outperformance=_boolean(
                True, "Synthetic five-year total return exceeded the benchmark."
            ),
            moat_and_management=_boolean(
                True, "Synthetic pricing-power and governance evidence is positive."
            ),
        ),
        valuation_anchors=(
            ValuationAnchor(
                method="dcf",
                current_price=Decimal("100"),
                fair_value=Decimal("125"),
                currency="EUR",
                as_of=REVIEW_DATE,
                source_ids=(source.id,),
                rationale="Synthetic discounted cash-flow estimate.",
            ),
        ),
        sources=(source,),
    )
    return replace(base, **changes)


class EquityReviewTests(unittest.TestCase):
    def test_public_equity_example_parses_and_reproduces_result(self) -> None:
        state = state_from_dict(_read(EXAMPLES / "equity-portfolio.example.json"))
        review_input = equity_review_input_from_dict(
            _read(EXAMPLES / "equity-evidence.example.json")
        )
        result = review_equity(state, review_input)

        self.assertEqual(
            to_json_value(result),
            _read(EXAMPLES / "equity-review.example.json"),
        )

    def test_full_quality_score_and_valuation_are_separate(self) -> None:
        result = review_equity(_stock_state(), _review_input())

        self.assertEqual(result.identity_status, "matched")
        self.assertEqual(result.hard_screen_status, "passed")
        self.assertEqual(result.points_awarded, Decimal("11"))
        self.assertEqual(result.points_available, Decimal("11"))
        self.assertEqual(result.score_percent, Decimal("100.0"))
        self.assertEqual(result.quality_classification, "quality")
        self.assertEqual(result.valuation.status, "acceptable")
        self.assertEqual(result.valuation.margin_of_safety, Decimal("0.2"))
        self.assertEqual(result.conclusion, "eligible_for_consideration")
        self.assertFalse(result.mutation_performed)

    def test_identity_mismatch_fails_before_scoring(self) -> None:
        review_input = _review_input(
            identity=replace(_review_input().identity, isin="IE00SYNTH043")
        )

        with self.assertRaisesRegex(ValidationError, "ISIN"):
            review_equity(_stock_state(), review_input)

    def test_three_missing_criteria_make_score_incomplete(self) -> None:
        quality = replace(
            _review_input().quality,
            institutional_ownership=None,
            benchmark_outperformance=None,
            moat_and_management=None,
        )
        result = review_equity(_stock_state(), _review_input(quality=quality))

        self.assertEqual(result.criteria_available, 5)
        self.assertEqual(result.score_status, "incomplete")
        self.assertEqual(result.quality_classification, "not_applied")
        self.assertEqual(result.conclusion, "insufficient_evidence")

    def test_missing_debt_to_ebitda_defers_threshold_classification(self) -> None:
        quality = replace(_review_input().quality, debt_to_ebitda=None)
        result = review_equity(_stock_state(), _review_input(quality=quality))

        self.assertEqual(result.score_status, "incomplete")
        self.assertEqual(result.quality_classification, "not_applied")
        self.assertIn("Debt/EBITDA", " ".join(result.limitations))

    def test_negative_current_free_cash_flow_fails_hard_screen(self) -> None:
        source_id = _review_input().sources[0].id
        quality = replace(
            _review_input().quality,
            free_cash_flow=(
                FreeCashFlowObservation("2024-12-31", Decimal("20"), source_id),
                FreeCashFlowObservation("2025-12-31", Decimal("-5"), source_id),
            ),
        )
        result = review_equity(_stock_state(), _review_input(quality=quality))

        self.assertEqual(result.hard_screen_status, "failed")
        self.assertEqual(result.criteria, ())
        self.assertEqual(result.conclusion, "hard_screen_failed")

    def test_prior_negative_free_cash_flow_is_not_scored_as_stable_growth(self) -> None:
        source_id = _review_input().sources[0].id
        quality = replace(
            _review_input().quality,
            free_cash_flow=(
                FreeCashFlowObservation("2023-12-31", Decimal("-10"), source_id),
                FreeCashFlowObservation("2024-12-31", Decimal("120"), source_id),
                FreeCashFlowObservation("2025-12-31", Decimal("140"), source_id),
            ),
        )
        result = review_equity(_stock_state(), _review_input(quality=quality))
        fcf = next(
            item for item in result.criteria if item.criterion == "free_cash_flow"
        )

        self.assertEqual(fcf.points_awarded, Decimal("1"))

    def test_negative_debt_ratio_is_rejected_as_non_meaningful(self) -> None:
        quality = replace(
            _review_input().quality,
            debt_to_ebitda=_decimal("-1"),
        )
        with self.assertRaisesRegex(ValidationError, "Debt/EBITDA"):
            review_equity(_stock_state(), _review_input(quality=quality))

    def test_capex_ratio_above_one_is_valid_but_requires_owner_evidence(self) -> None:
        quality = replace(
            _review_input().quality,
            capex_to_revenue=_decimal("1.2"),
        )
        result = review_equity(_stock_state(), _review_input(quality=quality))

        self.assertEqual(result.owner_earnings.status, "unavailable")
        capex = next(
            item for item in result.criteria if item.criterion == "capex_to_revenue"
        )
        self.assertEqual(capex.points_awarded, 0)

    def test_owner_earnings_components_require_one_reporting_date(self) -> None:
        owner = OwnerEarningsEvidence(
            currency="EUR",
            reported_earnings=_decimal("100"),
            depreciation_and_amortization=replace(
                _decimal("20"), as_of="2026-01-30"
            ),
            maintenance_capex=_decimal("30"),
            growth_capex_funded_from_fcf=_boolean(
                True, "Synthetic free-cash-flow funding evidence."
            ),
        )
        quality = replace(
            _review_input().quality,
            capex_to_revenue=_decimal("0.20"),
            owner_earnings=owner,
        )

        with self.assertRaisesRegex(ValidationError, "same reporting date"):
            review_equity(_stock_state(), _review_input(quality=quality))

    def test_owner_earnings_outflow_components_cannot_be_negative(self) -> None:
        for field in ("depreciation_and_amortization", "maintenance_capex"):
            with self.subTest(field=field):
                owner = OwnerEarningsEvidence(
                    currency="EUR",
                    reported_earnings=_decimal("100"),
                    depreciation_and_amortization=_decimal("20"),
                    maintenance_capex=_decimal("30"),
                    growth_capex_funded_from_fcf=_boolean(
                        True, "Synthetic free-cash-flow funding evidence."
                    ),
                )
                owner = replace(owner, **{field: _decimal("-1")})
                quality = replace(
                    _review_input().quality,
                    capex_to_revenue=_decimal("0.20"),
                    owner_earnings=owner,
                )

                with self.assertRaisesRegex(ValidationError, "cannot be negative"):
                    review_equity(_stock_state(), _review_input(quality=quality))

    def test_funding_red_flag_prevents_an_eligible_conclusion(self) -> None:
        owner = OwnerEarningsEvidence(
            currency="EUR",
            reported_earnings=_decimal("100"),
            depreciation_and_amortization=_decimal("20"),
            maintenance_capex=_decimal("30"),
            growth_capex_funded_from_fcf=_boolean(
                False, "Synthetic growth CapEx requires external funding."
            ),
        )
        quality = replace(
            _review_input().quality,
            capex_to_revenue=_decimal("0.20"),
            owner_earnings=owner,
        )

        result = review_equity(_stock_state(), _review_input(quality=quality))

        self.assertEqual(result.quality_classification, "quality")
        self.assertEqual(result.owner_earnings.status, "funding_red_flag")
        self.assertEqual(result.conclusion, "funding_red_flag")

    def test_conflicting_valuation_directions_are_not_averaged(self) -> None:
        first = _review_input().valuation_anchors[0]
        second = replace(
            first,
            method="forward_pe",
            fair_value=Decimal("90"),
            rationale="Synthetic peer-multiple estimate.",
        )
        result = review_equity(
            _stock_state(),
            _review_input(valuation_anchors=(first, second)),
        )

        self.assertEqual(result.valuation.status, "conflicting")
        self.assertEqual(result.valuation.selected_method, "dcf")
        self.assertEqual(result.conclusion, "insufficient_valuation")

    def test_consensus_price_target_is_not_an_allowed_anchor(self) -> None:
        invalid = replace(
            _review_input().valuation_anchors[0], method="consensus_price_target"
        )
        with self.assertRaisesRegex(ValidationError, "valuation method"):
            review_equity(
                _stock_state(), _review_input(valuation_anchors=(invalid,))
            )

    def test_valuation_comparison_requires_one_price_and_date(self) -> None:
        first = _review_input().valuation_anchors[0]
        second = replace(
            first,
            method="forward_pe",
            current_price=Decimal("101"),
        )
        with self.assertRaisesRegex(ValidationError, "one as-of date and current price"):
            review_equity(
                _stock_state(), _review_input(valuation_anchors=(first, second))
            )

    def test_parser_rejects_non_string_financial_decimals(self) -> None:
        raw = _read(EXAMPLES / "equity-evidence.example.json")
        raw["quality"]["revenue_growth"]["value"] = 0.12
        with self.assertRaisesRegex(ValidationError, "canonical decimal string"):
            equity_review_input_from_dict(raw)

    def test_untracked_external_dependency_limits_conclusion(self) -> None:
        circle = replace(
            _review_input().circle_of_competence,
            external_dependency="A synthetic regulatory approval.",
            observable_event=None,
        )
        result = review_equity(
            _stock_state(), _review_input(circle_of_competence=circle)
        )

        self.assertEqual(result.circle_of_competence.status, "untracked_dependency")
        self.assertEqual(result.conclusion, "insufficient_evidence")

    def test_stale_decision_evidence_defers_the_conclusion(self) -> None:
        result = review_equity(
            _stock_state(),
            _review_input(as_of="2026-02-10"),
        )

        self.assertEqual(result.source_assessments[0].freshness, "stale")
        self.assertEqual(result.conclusion, "insufficient_evidence")

    def test_result_is_json_compatible(self) -> None:
        payload = to_json_value(review_equity(_stock_state(), _review_input()))
        self.assertEqual(payload["score_percent"], "100")
        self.assertEqual(payload["valuation"]["margin_of_safety"], "0.2")

    def test_private_equity_review_save_is_non_overwriting(self) -> None:
        result = review_equity(_stock_state(), _review_input())
        with tempfile.TemporaryDirectory() as temporary:
            path = save_equity_review(temporary, result)
            self.assertEqual(path.parent.name, "reviews")
            self.assertEqual(path.parent.parent.name, "private")
            self.assertEqual(_read(path), to_json_value(result))
            with self.assertRaises(FileExistsError):
                save_equity_review(temporary, result)

    def test_private_save_rejects_an_inconsistent_constructed_result(self) -> None:
        result = review_equity(_stock_state(), _review_input())
        invalid = replace(result, points_awarded=Decimal("10"))
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValidationError, "point totals"):
                save_equity_review(temporary, invalid)


class InstrumentIdentityTests(unittest.TestCase):
    def test_duplicate_isin_cannot_create_two_economic_instruments(self) -> None:
        state = _stock_state()
        duplicate = Instrument(
            id="instrument-duplicate",
            name="Synthetic Duplicate",
            kind="stock",
            economic_currency="EUR",
            isin=state.instruments[0].isin,
        )
        listing = Listing(
            id="listing-duplicate",
            instrument_id=duplicate.id,
            mic="XPAR",
            ticker="SYN2",
            trading_currency="EUR",
        )

        with self.assertRaisesRegex(ValidationError, "Duplicate ISIN"):
            validate_state(
                replace(
                    state,
                    instruments=(*state.instruments, duplicate),
                    listings=(*state.listings, listing),
                )
            )


class PortfolioPolicyTests(unittest.TestCase):
    def _analysis(self):
        state = state_from_dict(_read(EXAMPLES / "portfolio.example.json"))
        market = _read(EXAMPLES / "market-input.example.json")
        return state, analyze_portfolio(
            state,
            market_prices_from_dict(market["prices"]),
            fx_rates_from_dict(market["fx_rates"]),
            REVIEW_DATE,
        )

    def test_policy_exemptions_and_private_thresholds_are_explicit(self) -> None:
        state, analysis = self._analysis()
        policy = PortfolioPolicy(
            id="synthetic-policy",
            version="1.0",
            analysis_base="invested_positions",
            max_direct_weight=Decimal("0.15"),
            direct_weight_exempt_instrument_ids=("instrument-global",),
            fragmentation_weight_threshold=Decimal("0.20"),
            max_fragmented_positions=0,
            satellite_instrument_ids=("instrument-bond",),
            max_satellite_weight=Decimal("0.15"),
            factor_groups=(
                FactorGroupPolicy(
                    id="synthetic-shared-factor",
                    instrument_ids=("instrument-global", "instrument-bond"),
                    previous_reported_weight=Decimal("0.95"),
                    change_alert_threshold=Decimal("0.05"),
                ),
            ),
        )

        result = evaluate_portfolio_policy(state, analysis, policy)

        self.assertNotIn("instrument-global", result.direct_weight_breaches)
        self.assertIn("instrument-bond", result.direct_weight_breaches)
        self.assertTrue(result.satellite_limit_breached)
        self.assertEqual(result.factor_groups[0].current_weight, Decimal("1"))
        self.assertFalse(result.factor_groups[0].change_alert)
        self.assertEqual(result.analysis_base, "invested_positions")

    def test_unknown_private_policy_instrument_is_rejected(self) -> None:
        state, analysis = self._analysis()
        policy = PortfolioPolicy(
            id="synthetic-policy",
            version="1.0",
            analysis_base="invested_positions",
            max_direct_weight=Decimal("0.15"),
            direct_weight_exempt_instrument_ids=("missing",),
            fragmentation_weight_threshold=Decimal("0.02"),
            max_fragmented_positions=5,
            satellite_instrument_ids=(),
            max_satellite_weight=Decimal("0.30"),
        )

        with self.assertRaisesRegex(ValidationError, "unknown instrument"):
            evaluate_portfolio_policy(state, analysis, policy)

    def test_policy_rejects_invalid_analysis_invariants(self) -> None:
        state, analysis = self._analysis()
        policy = portfolio_policy_from_dict(
            _read(EXAMPLES / "portfolio-policy.example.json")
        )
        first, second = analysis.positions
        invalid_analyses = (
            replace(analysis, positions=(first, first)),
            replace(
                analysis,
                positions=(replace(first, current_weight=Decimal("NaN")), second),
            ),
            replace(
                analysis,
                positions=(
                    replace(
                        first,
                        current_weight=Decimal("0.7"),
                        drift=Decimal("0.2"),
                    ),
                    second,
                ),
                maximum_direct_weight=Decimal("0.7"),
                herfindahl_index=Decimal("0.53"),
            ),
        )

        for invalid in invalid_analyses:
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValidationError):
                    evaluate_portfolio_policy(state, invalid, policy)

    def test_policy_requires_complete_current_state_coverage(self) -> None:
        state, analysis = self._analysis()
        approved = next(
            allocation
            for allocation in state.target_allocations
            if allocation.status == "approved"
        )
        zero_weight_target = replace(
            approved.targets[0],
            instrument_id="instrument-policy-benchmark",
            weight=Decimal("0"),
        )
        expanded_approved = replace(
            approved,
            targets=(*approved.targets, zero_weight_target),
        )
        expanded_state = replace(
            state,
            target_allocations=tuple(
                expanded_approved if allocation.id == approved.id else allocation
                for allocation in state.target_allocations
            ),
        )
        policy = portfolio_policy_from_dict(
            _read(EXAMPLES / "portfolio-policy.example.json")
        )

        with self.assertRaisesRegex(ValidationError, "coverage"):
            evaluate_portfolio_policy(expanded_state, analysis, policy)

    def test_public_policy_example_parses_and_reproduces_result(self) -> None:
        state, analysis = self._analysis()
        policy = portfolio_policy_from_dict(
            _read(EXAMPLES / "portfolio-policy.example.json")
        )

        result = evaluate_portfolio_policy(state, analysis, policy)

        self.assertEqual(
            to_json_value(result),
            _read(EXAMPLES / "portfolio-policy-result.example.json"),
        )

        with tempfile.TemporaryDirectory() as temporary:
            path = save_portfolio_policy_result(temporary, result)
            self.assertEqual(path.parent.name, "reviews")
            self.assertEqual(_read(path), to_json_value(result))


if __name__ == "__main__":
    unittest.main()
