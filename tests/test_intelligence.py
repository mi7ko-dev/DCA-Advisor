"""Deterministic Phase 4 portfolio-intelligence tests with synthetic data."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import fields, replace
from decimal import Decimal
import json
from pathlib import Path
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from steadyfolio.calculations import analyze_portfolio  # noqa: E402
from steadyfolio.errors import ValidationError  # noqa: E402
from steadyfolio.intelligence import analyze_portfolio_intelligence  # noqa: E402
from steadyfolio.intelligence_reporting import (  # noqa: E402
    render_intelligence_report,
    render_thesis_review_report,
)
from steadyfolio.models import to_json_value  # noqa: E402
from steadyfolio.providers import ResearchProvider, StaticResearchProvider  # noqa: E402
from steadyfolio.research_models import (  # noqa: E402
    ResearchRequest,
    ResearchSnapshot,
)
from steadyfolio.research_validation import (  # noqa: E402
    research_snapshot_from_dict,
    stress_windows_from_dict,
    thesis_evidence_from_dict,
    validate_research_snapshot,
)
from steadyfolio.storage import (  # noqa: E402
    save_intelligence_result,
    save_thesis_review,
)
from steadyfolio.thesis import review_investment_thesis  # noqa: E402
from steadyfolio.validation import (  # noqa: E402
    fx_rates_from_dict,
    market_prices_from_dict,
    state_from_dict,
    validate_state,
)


EXAMPLES = REPOSITORY_ROOT / "examples"
ANALYSIS_DATE = "2026-01-31"


def _read(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _inputs():
    state = state_from_dict(_read(EXAMPLES / "portfolio.example.json"))
    market = _read(EXAMPLES / "market-input.example.json")
    analysis = analyze_portfolio(
        state,
        market_prices_from_dict(market["prices"]),
        fx_rates_from_dict(market["fx_rates"]),
        ANALYSIS_DATE,
    )
    snapshot = research_snapshot_from_dict(
        _read(EXAMPLES / "research-snapshot.example.json")
    )
    stress = stress_windows_from_dict(
        _read(EXAMPLES / "stress-windows.example.json")
    )
    return state, analysis, snapshot, stress


def _thesis_input():
    raw = _read(EXAMPLES / "thesis-evidence.example.json")
    return raw, thesis_evidence_from_dict(raw["evidence"])


class ProviderAndValidationTests(unittest.TestCase):
    def test_static_provider_implements_minimal_replaceable_interface(self) -> None:
        state, _, snapshot, _ = _inputs()
        provider = StaticResearchProvider("Synthetic Provider", snapshot)
        self.assertIsInstance(provider, ResearchProvider)
        self.assertEqual(
            {field.name for field in fields(ResearchRequest)},
            {"instrument_ids", "listing_ids", "as_of"},
        )
        supplied = provider.fetch(
            ResearchRequest(
                instrument_ids=tuple(item.id for item in state.instruments),
                listing_ids=tuple(item.id for item in state.listings),
                as_of=ANALYSIS_DATE,
            )
        )
        self.assertEqual(supplied, snapshot)

        filtered = provider.fetch(
            ResearchRequest(
                instrument_ids=("instrument-global",),
                listing_ids=("listing-global-xetr",),
                as_of=ANALYSIS_DATE,
            )
        )
        self.assertTrue(
            all(item.instrument_id == "instrument-global" for item in filtered.funds)
        )
        self.assertTrue(
            all(
                item.fund_instrument_id == "instrument-global"
                for item in filtered.fund_holdings
            )
        )
        self.assertEqual(
            {item.listing_id for item in filtered.historical_series},
            {"listing-global-xetr"},
        )

    def test_research_snapshot_rejects_overstated_holdings_coverage(self) -> None:
        _, _, snapshot, _ = _inputs()
        first = replace(snapshot.fund_holdings[0], weight=Decimal("0.95"))
        invalid = replace(
            snapshot, fund_holdings=(first,) + snapshot.fund_holdings[1:]
        )
        with self.assertRaisesRegex(ValidationError, "coverage cannot exceed one"):
            validate_research_snapshot(invalid)

    def test_research_snapshot_rejects_binary_float(self) -> None:
        raw = deepcopy(_read(EXAMPLES / "research-snapshot.example.json"))
        raw["funds"][0]["ter"] = 0.002
        with self.assertRaisesRegex(ValidationError, "decimal string"):
            research_snapshot_from_dict(raw)

    def test_thesis_target_must_match_approved_policy(self) -> None:
        state, _, _, _ = _inputs()
        invalid = replace(state.investment_theses[0], target_weight=Decimal("0.4"))
        with self.assertRaisesRegex(ValidationError, "approved allocation"):
            validate_state(
                replace(
                    state,
                    investment_theses=(invalid,) + state.investment_theses[1:],
                )
            )

    def test_research_source_cannot_predate_its_data(self) -> None:
        _, _, snapshot, _ = _inputs()
        invalid_source = replace(
            snapshot.sources[0], retrieved_at="2026-01-14T18:00:00+00:00"
        )
        with self.assertRaisesRegex(ValidationError, "retrieved before"):
            validate_research_snapshot(
                replace(snapshot, sources=(invalid_source,) + snapshot.sources[1:])
            )


class PortfolioIntelligenceTests(unittest.TestCase):
    def test_modified_portfolio_analysis_is_rejected(self) -> None:
        state, analysis, snapshot, stress = _inputs()
        first = replace(analysis.positions[0], drift=Decimal("0"))
        modified = replace(analysis, positions=(first,) + analysis.positions[1:])
        with self.assertRaisesRegex(ValidationError, "drift is stale or modified"):
            analyze_portfolio_intelligence(
                state, modified, snapshot, ANALYSIS_DATE, stress
            )

    def test_overlap_concentration_and_exposure_keep_missing_coverage_visible(self) -> None:
        state, analysis, snapshot, stress = _inputs()
        result = analyze_portfolio_intelligence(
            state, analysis, snapshot, ANALYSIS_DATE, stress
        )

        self.assertEqual(result.overlaps[0].observed_overlap_weight, Decimal("0.05"))
        self.assertEqual(result.overlaps[0].left_holdings_coverage, Decimal("0.23"))
        self.assertEqual(result.overlaps[0].right_holdings_coverage, Decimal("0.10"))
        self.assertEqual(
            result.company_concentration.covered_portfolio_weight, Decimal("0.204")
        )
        self.assertEqual(
            result.company_concentration.unclassified_portfolio_weight,
            Decimal("0.796"),
        )
        self.assertEqual(
            {item.dimension for item in result.exposures},
            {"sector", "geography", "currency"},
        )
        self.assertTrue(
            all(
                item.covered_portfolio_weight == Decimal("0.204")
                and item.unclassified_portfolio_weight == Decimal("0.796")
                for item in result.exposures
            )
        )

    def test_source_freshness_and_terms_are_retained(self) -> None:
        state, analysis, snapshot, stress = _inputs()
        result = analyze_portfolio_intelligence(
            state, analysis, snapshot, ANALYSIS_DATE, stress
        )
        assessments = {item.source_id: item for item in result.source_assessments}

        self.assertEqual(assessments["synthetic-fund-holdings"].freshness, "stale")
        self.assertEqual(assessments["synthetic-fund-holdings"].age_days, 31)
        self.assertEqual(
            assessments["synthetic-fund-holdings"].terms_reference,
            "project-generated-synthetic-data",
        )
        self.assertTrue(assessments["synthetic-fund-holdings"].cache_permitted)
        self.assertIn(
            "Research source synthetic-fund-holdings is stale at 31 days old.",
            result.warnings,
        )

    def test_historical_metrics_use_aligned_total_return_series(self) -> None:
        state, analysis, snapshot, stress = _inputs()
        result = analyze_portfolio_intelligence(
            state, analysis, snapshot, ANALYSIS_DATE, stress
        )
        metrics = {item.instrument_id: item for item in result.historical_metrics}

        self.assertEqual(metrics["instrument-global"].cumulative_return, Decimal("0.2"))
        self.assertEqual(metrics["instrument-global"].maximum_drawdown, Decimal("0.1"))
        self.assertEqual(metrics["instrument-global"].excess_return, Decimal("0.02"))
        self.assertEqual(metrics["instrument-global"].frequency, "monthly")
        self.assertEqual(metrics["instrument-global"].return_convention, "total_return_index")
        self.assertEqual(len(result.correlations), 1)
        self.assertGreaterEqual(result.correlations[0].correlation, Decimal("-1"))
        self.assertLessEqual(result.correlations[0].correlation, Decimal("1"))
        self.assertEqual(len(result.stress_metrics), 2)

    def test_incompatible_historical_currency_is_rejected(self) -> None:
        state, analysis, snapshot, stress = _inputs()
        changed = replace(snapshot.historical_series[1], currency="USD")
        invalid = replace(
            snapshot,
            historical_series=(snapshot.historical_series[0], changed)
            + snapshot.historical_series[2:],
        )
        with self.assertRaisesRegex(ValidationError, "base currency"):
            analyze_portfolio_intelligence(
                state, analysis, invalid, ANALYSIS_DATE, stress
            )

    def test_incompatible_historical_period_is_rejected(self) -> None:
        state, analysis, snapshot, stress = _inputs()
        changed = replace(
            snapshot.historical_series[1],
            observations=snapshot.historical_series[1].observations[1:],
        )
        invalid = replace(
            snapshot,
            historical_series=(snapshot.historical_series[0], changed)
            + snapshot.historical_series[2:],
        )
        with self.assertRaisesRegex(ValidationError, "compatible dates"):
            analyze_portfolio_intelligence(
                state, analysis, invalid, ANALYSIS_DATE, stress
            )

    def test_missing_currency_evidence_is_reported_not_zero_filled(self) -> None:
        state, analysis, snapshot, stress = _inputs()
        partial = replace(
            snapshot,
            classified_exposures=tuple(
                item
                for item in snapshot.classified_exposures
                if item.dimension != "currency"
            ),
        )
        result = analyze_portfolio_intelligence(
            state, analysis, partial, ANALYSIS_DATE, stress
        )
        self.assertNotIn("currency", {item.dimension for item in result.exposures})
        self.assertIn(
            "Currency exposure is unavailable; missing data was not treated as zero.",
            result.warnings,
        )

    def test_missing_provider_data_preserves_offline_portfolio_analysis(self) -> None:
        state, analysis, _, _ = _inputs()
        empty = ResearchSnapshot("1.0", (), (), (), (), ())
        result = analyze_portfolio_intelligence(
            state, analysis, empty, ANALYSIS_DATE
        )
        self.assertEqual(result.company_concentration.covered_portfolio_weight, 0)
        self.assertEqual(result.company_concentration.unclassified_portfolio_weight, 1)
        self.assertEqual(result.historical_metrics, ())
        self.assertIn("Historical data is unavailable for instrument-global.", result.warnings)

    def test_future_source_data_is_rejected(self) -> None:
        state, analysis, snapshot, stress = _inputs()
        future_source = replace(
            snapshot.sources[0],
            as_of="2026-02-01",
            retrieved_at="2026-02-01T18:00:00+00:00",
        )
        future_funds = tuple(
            replace(item, as_of="2026-02-01")
            if item.source_id == future_source.id
            else item
            for item in snapshot.funds
        )
        invalid = replace(
            snapshot,
            sources=(future_source,) + snapshot.sources[1:],
            funds=future_funds,
        )
        with self.assertRaisesRegex(ValidationError, "newer than the analysis date"):
            analyze_portfolio_intelligence(
                state, analysis, invalid, ANALYSIS_DATE, stress
            )

    def test_direct_stock_is_counted_as_observed_company_exposure(self) -> None:
        state, analysis, snapshot, stress = _inputs()
        stock = replace(state.instruments[1], kind="stock")
        stock_state = replace(
            state,
            instruments=(state.instruments[0], stock) + state.instruments[2:],
        )
        stock_snapshot = replace(
            snapshot,
            funds=tuple(
                item for item in snapshot.funds if item.instrument_id != stock.id
            ),
            fund_holdings=tuple(
                item
                for item in snapshot.fund_holdings
                if item.fund_instrument_id != stock.id
            ),
        )
        result = analyze_portfolio_intelligence(
            stock_state, analysis, stock_snapshot, ANALYSIS_DATE, stress
        )
        exposures = {
            item.constituent_id: item.observed_portfolio_weight
            for item in result.company_concentration.exposures
        }
        self.assertEqual(exposures[stock.id], Decimal("0.2"))


class ThesisReviewTests(unittest.TestCase):
    def test_price_decline_alone_does_not_fail_or_mutate_thesis(self) -> None:
        state, _, snapshot, _ = _inputs()
        raw, evidence = _thesis_input()
        original = deepcopy(state)
        review = review_investment_thesis(
            state,
            raw["thesis_id"],
            evidence,
            raw["observed_review_triggers"],
            raw["reviewed_at"],
            snapshot,
        )
        self.assertEqual(review.proposed_action, "retain")
        self.assertIn("price movement alone", review.interpretations[1])
        self.assertEqual(state, original)

    def test_configured_trigger_proposes_review_without_policy_change(self) -> None:
        state, _, snapshot, _ = _inputs()
        raw, evidence = _thesis_input()
        review = review_investment_thesis(
            state,
            raw["thesis_id"],
            evidence,
            ("Index methodology changes",),
            raw["reviewed_at"],
            snapshot,
        )
        self.assertEqual(review.proposed_action, "review")
        self.assertEqual(
            review.triggered_review_conditions, ("Index methodology changes",)
        )
        self.assertIn("do not mutate holdings or targets", review.proposed_changes[0])

    def test_review_without_evidence_requests_investigation(self) -> None:
        state, _, snapshot, _ = _inputs()
        review = review_investment_thesis(
            state, "thesis-global", (), (), ANALYSIS_DATE, snapshot
        )
        self.assertEqual(review.proposed_action, "investigate")
        self.assertTrue(
            any("No evidence was supplied" in item for item in review.limitations)
        )


class OutputTests(unittest.TestCase):
    def test_structured_outputs_have_documented_root_fields(self) -> None:
        state, analysis, snapshot, stress = _inputs()
        result = analyze_portfolio_intelligence(
            state, analysis, snapshot, ANALYSIS_DATE, stress
        )
        raw, evidence = _thesis_input()
        review = review_investment_thesis(
            state,
            raw["thesis_id"],
            evidence,
            raw["observed_review_triggers"],
            raw["reviewed_at"],
            snapshot,
        )
        for schema_name, value in (
            ("intelligence-result.schema.json", result),
            ("thesis-review.schema.json", review),
        ):
            with self.subTest(schema=schema_name):
                schema = _read(REPOSITORY_ROOT / "schemas" / schema_name)
                self.assertTrue(set(schema["required"]).issubset(to_json_value(value)))

    def test_reports_separate_coverage_evidence_and_interpretation(self) -> None:
        state, analysis, snapshot, stress = _inputs()
        result = analyze_portfolio_intelligence(
            state, analysis, snapshot, ANALYSIS_DATE, stress
        )
        raw, evidence = _thesis_input()
        review = review_investment_thesis(
            state,
            raw["thesis_id"],
            evidence,
            raw["observed_review_triggers"],
            raw["reviewed_at"],
            snapshot,
        )
        intelligence_report = render_intelligence_report(state, result)
        thesis_report = render_thesis_review_report(state, review)
        self.assertIn("Unclassified portfolio weight: 79.60%", intelligence_report)
        self.assertIn("not presented as complete look-through", intelligence_report)
        self.assertIn("## Evidence facts", thesis_report)
        self.assertIn("## Interpretation", thesis_report)
        self.assertIn("does not mutate holdings", thesis_report)

    def test_private_intelligence_and_review_outputs_stay_below_private(self) -> None:
        state, analysis, snapshot, stress = _inputs()
        result = analyze_portfolio_intelligence(
            state, analysis, snapshot, ANALYSIS_DATE, stress
        )
        raw, evidence = _thesis_input()
        review = review_investment_thesis(
            state,
            raw["thesis_id"],
            evidence,
            raw["observed_review_triggers"],
            raw["reviewed_at"],
            snapshot,
        )
        with tempfile.TemporaryDirectory(prefix="steadyfolio-phase4-") as temporary:
            workspace = Path(temporary)
            intelligence_path = save_intelligence_result(workspace, result)
            review_path = save_thesis_review(workspace, review)
            self.assertTrue(intelligence_path.is_relative_to(workspace / "private"))
            self.assertTrue(review_path.is_relative_to(workspace / "private"))
            self.assertEqual(
                json.loads(intelligence_path.read_text(encoding="utf-8"))["id"],
                result.id,
            )


if __name__ == "__main__":
    unittest.main()
