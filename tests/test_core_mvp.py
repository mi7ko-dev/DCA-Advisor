"""Deterministic Phase 3 MVP tests using synthetic data only."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from steadyfolio.calculations import analyze_portfolio, plan_contribution  # noqa: E402
from steadyfolio.errors import (  # noqa: E402
    MissingFxRateError,
    MissingPriceError,
    StorageSafetyError,
    ValidationError,
)
from steadyfolio.models import (  # noqa: E402
    Account,
    AllocationTarget,
    DataSource,
    FxRate,
    Holding,
    Instrument,
    InvestorProfile,
    Listing,
    MarketPrice,
    PortfolioState,
    TargetAllocation,
    Transaction,
    TradingConstraint,
    to_json_value,
)
from steadyfolio.reporting import (  # noqa: E402
    render_analysis_report,
    render_contribution_report,
)
from steadyfolio.storage import (  # noqa: E402
    initialize_workspace,
    load_state,
    save_analysis_result,
    save_contribution_plan,
    save_report,
    save_state,
)
from steadyfolio.validation import (  # noqa: E402
    constraints_from_dict,
    fx_rates_from_dict,
    market_prices_from_dict,
    state_from_dict,
    state_to_dict,
    validate_state,
)


EXAMPLES = REPOSITORY_ROOT / "examples"
VALUATION_DATE = "2026-01-31"


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _example_inputs() -> tuple[
    PortfolioState,
    tuple[MarketPrice, ...],
    tuple[FxRate, ...],
    tuple[TradingConstraint, ...],
]:
    state = state_from_dict(_read_json(EXAMPLES / "portfolio.example.json"))
    market = _read_json(EXAMPLES / "market-input.example.json")
    request = _read_json(EXAMPLES / "contribution-request.example.json")
    return (
        state,
        market_prices_from_dict(market["prices"]),
        fx_rates_from_dict(market["fx_rates"]),
        constraints_from_dict(request["constraints"]),
    )


def _multi_currency_state() -> PortfolioState:
    source_price = DataSource(
        id="source-prices",
        provider="Synthetic Fixture Provider",
        source_type="market_snapshot",
        value_time="2026-01-31T16:00:00+00:00",
        retrieved_at="2026-01-31T17:00:00+00:00",
        reference="synthetic-prices",
        quality="synthetic",
    )
    source_fx = replace(
        source_price,
        id="source-fx",
        source_type="fx_snapshot",
        reference="synthetic-fx",
    )
    return PortfolioState(
        schema_version="1.0",
        investor_profile=InvestorProfile(
            id="synthetic-multi-currency",
            base_currency="EUR",
            jurisdiction="EU-SYNTHETIC",
        ),
        instruments=(
            Instrument(
                id="instrument-eur",
                name="Synthetic EUR Asset",
                kind="etf",
                economic_currency="EUR",
            ),
            Instrument(
                id="instrument-usd",
                name="Synthetic USD Asset",
                kind="stock",
                economic_currency="USD",
            ),
        ),
        listings=(
            Listing(
                id="listing-eur",
                instrument_id="instrument-eur",
                mic="XETR",
                ticker="SEUR",
                trading_currency="EUR",
            ),
            Listing(
                id="listing-usd",
                instrument_id="instrument-usd",
                mic="XLON",
                ticker="SUSD",
                trading_currency="USD",
            ),
        ),
        accounts=(
            Account(
                id="synthetic-account",
                name="Synthetic Account",
                kind="brokerage",
                currency="EUR",
            ),
        ),
        holdings=(
            Holding(
                id="holding-eur",
                account_id="synthetic-account",
                listing_id="listing-eur",
                quantity=Decimal("1"),
            ),
            Holding(
                id="holding-usd",
                account_id="synthetic-account",
                listing_id="listing-usd",
                quantity=Decimal("1"),
            ),
        ),
        target_allocations=(
            TargetAllocation(
                id="approved-target",
                status="approved",
                effective_date="2026-01-01",
                targets=(
                    AllocationTarget("instrument-eur", Decimal("0.5")),
                    AllocationTarget("instrument-usd", Decimal("0.5")),
                ),
            ),
        ),
        data_sources=(source_price, source_fx),
    )


class SchemaAndValidationTests(unittest.TestCase):
    def test_public_schema_documents_are_valid_json(self) -> None:
        schemas = sorted((REPOSITORY_ROOT / "schemas").glob("*.schema.json"))
        self.assertEqual(
            {schema.name for schema in schemas},
            {
                "analysis-result.schema.json",
                "committee-result.schema.json",
                "contribution-plan.schema.json",
                "equity-evidence.schema.json",
                "equity-review.schema.json",
                "intelligence-result.schema.json",
                "market-input.schema.json",
                "portfolio.schema.json",
                "portfolio-policy-result.schema.json",
                "portfolio-policy.schema.json",
                "research-snapshot.schema.json",
                "thesis-review.schema.json",
            },
        )
        for schema in schemas:
            with self.subTest(schema=schema.name):
                parsed = _read_json(schema)
                self.assertEqual(parsed["$schema"], "https://json-schema.org/draft/2020-12/schema")

    def test_example_state_round_trips_without_float_values(self) -> None:
        state, _, _, _ = _example_inputs()
        serialized = state_to_dict(state)
        self.assertEqual(state_from_dict(serialized), state)

        def assert_no_float(value: object) -> None:
            self.assertNotIsInstance(value, float)
            if isinstance(value, dict):
                for child in value.values():
                    assert_no_float(child)
            elif isinstance(value, list):
                for child in value:
                    assert_no_float(child)

        assert_no_float(serialized)

    def test_decimal_json_fields_reject_binary_float(self) -> None:
        raw = deepcopy(_read_json(EXAMPLES / "portfolio.example.json"))
        raw["holdings"][0]["quantity"] = 8.0
        with self.assertRaisesRegex(ValidationError, "decimal string"):
            state_from_dict(raw)

    def test_decimal_json_fields_reject_noncanonical_strings(self) -> None:
        raw = deepcopy(_read_json(EXAMPLES / "portfolio.example.json"))
        for value in ("8e-3", "+0.008", " 0.008", "0_008"):
            with self.subTest(value=value):
                changed = deepcopy(raw)
                changed["instruments"][0]["annual_fee_rate"] = value
                with self.assertRaisesRegex(ValidationError, "canonical decimal"):
                    state_from_dict(changed)

    def test_public_timestamps_require_a_timezone_offset(self) -> None:
        raw = deepcopy(_read_json(EXAMPLES / "portfolio.example.json"))
        for value in ("2026-01-31", "2026-01-31T18:00:00"):
            with self.subTest(value=value):
                changed = deepcopy(raw)
                changed["data_sources"][0]["retrieved_at"] = value
                with self.assertRaisesRegex(ValidationError, "timezone-aware"):
                    state_from_dict(changed)

    def test_unknown_state_fields_are_rejected(self) -> None:
        raw = deepcopy(_read_json(EXAMPLES / "portfolio.example.json"))
        raw["private_note"] = "must not be silently retained"
        with self.assertRaisesRegex(ValidationError, "unknown fields"):
            state_from_dict(raw)

    def test_duplicate_listing_identity_is_rejected(self) -> None:
        state, _, _, _ = _example_inputs()
        duplicate = replace(
            state.listings[1],
            id="listing-duplicate",
            ticker=state.listings[0].ticker,
            mic=state.listings[0].mic,
        )
        with self.assertRaisesRegex(ValidationError, "Duplicate MIC"):
            validate_state(replace(state, listings=state.listings + (duplicate,)))

    def test_invalid_target_weight_total_is_rejected(self) -> None:
        state, _, _, _ = _example_inputs()
        invalid_allocation = replace(
            state.target_allocations[0],
            targets=(
                AllocationTarget("instrument-global", Decimal("0.6")),
                AllocationTarget("instrument-bond", Decimal("0.5")),
            ),
        )
        with self.assertRaisesRegex(ValidationError, "sum to one"):
            validate_state(
                replace(state, target_allocations=(invalid_allocation,))
            )

    def test_unsupported_instrument_kind_is_rejected(self) -> None:
        state, _, _, _ = _example_inputs()
        invalid = replace(state.instruments[0], kind="crypto")
        with self.assertRaisesRegex(ValidationError, "only ETF and stock"):
            validate_state(replace(state, instruments=(invalid,) + state.instruments[1:]))

    def test_transaction_price_currency_must_match_listing(self) -> None:
        state, _, _, _ = _example_inputs()
        transaction = Transaction(
            id="transaction-synthetic",
            account_id=state.accounts[0].id,
            listing_id=state.listings[0].id,
            kind="buy",
            trade_date="2026-01-02",
            quantity=Decimal("1"),
            unit_price=Decimal("100"),
            price_currency="USD",
            fees=Decimal("0"),
        )
        with self.assertRaisesRegex(ValidationError, "price currency differs"):
            validate_state(replace(state, transactions=(transaction,)))


class PortfolioAnalysisTests(unittest.TestCase):
    def test_equal_and_drifted_weights_use_documented_sign(self) -> None:
        state, prices, fx_rates, _ = _example_inputs()
        result = analyze_portfolio(state, prices, fx_rates, VALUATION_DATE)
        positions = {position.instrument_id: position for position in result.positions}

        self.assertEqual(result.total_value, Decimal("1000"))
        self.assertEqual(positions["instrument-global"].current_weight, Decimal("0.8"))
        self.assertEqual(positions["instrument-global"].drift, Decimal("0.3"))
        self.assertEqual(positions["instrument-bond"].current_weight, Decimal("0.2"))
        self.assertEqual(positions["instrument-bond"].drift, Decimal("-0.3"))
        self.assertEqual(result.weighted_annual_fee_rate, Decimal("0.00190"))
        self.assertEqual(result.herfindahl_index, Decimal("0.68"))

    def test_zero_holdings_are_explicit_not_divided_by_zero(self) -> None:
        state, prices, fx_rates, _ = _example_inputs()
        empty = replace(state, holdings=())
        result = analyze_portfolio(empty, prices, fx_rates, VALUATION_DATE)

        self.assertEqual(result.total_value, Decimal("0"))
        self.assertTrue(all(position.current_weight == 0 for position in result.positions))
        self.assertIn("Portfolio market value is zero.", result.warnings)

    def test_target_must_be_effective_on_valuation_date(self) -> None:
        state, prices, fx_rates, _ = _example_inputs()
        future_target = replace(
            state.target_allocations[0], effective_date="2026-02-01"
        )
        with self.assertRaisesRegex(ValidationError, "not effective"):
            analyze_portfolio(
                replace(state, target_allocations=(future_target,)),
                prices,
                fx_rates,
                VALUATION_DATE,
            )

    def test_multi_currency_valuation_uses_dated_fx(self) -> None:
        state = _multi_currency_state()
        prices = (
            MarketPrice("listing-eur", Decimal("100"), "EUR", VALUATION_DATE, "source-prices"),
            MarketPrice("listing-usd", Decimal("100"), "USD", VALUATION_DATE, "source-prices"),
        )
        rates = (
            FxRate("USD", "EUR", Decimal("0.9"), VALUATION_DATE, "source-fx"),
        )
        result = analyze_portfolio(state, prices, rates, VALUATION_DATE)

        self.assertEqual(result.total_value, Decimal("190"))
        self.assertEqual(set(result.source_ids), {"source-prices", "source-fx"})

    def test_newest_fx_quote_wins_across_direct_and_inverse_orientations(self) -> None:
        state = _multi_currency_state()
        prices = (
            MarketPrice("listing-eur", Decimal("100"), "EUR", VALUATION_DATE, "source-prices"),
            MarketPrice("listing-usd", Decimal("100"), "USD", VALUATION_DATE, "source-prices"),
        )
        rates = (
            FxRate("USD", "EUR", Decimal("0.9"), "2026-01-01", "source-fx"),
            FxRate("EUR", "USD", Decimal("2"), VALUATION_DATE, "source-fx"),
        )

        result = analyze_portfolio(state, prices, rates, VALUATION_DATE)

        self.assertEqual(result.total_value, Decimal("150"))

    def test_conflicting_same_date_fx_rates_are_rejected(self) -> None:
        state = _multi_currency_state()
        prices = (
            MarketPrice("listing-eur", Decimal("100"), "EUR", VALUATION_DATE, "source-prices"),
            MarketPrice("listing-usd", Decimal("100"), "USD", VALUATION_DATE, "source-prices"),
        )
        rates = (
            FxRate("USD", "EUR", Decimal("0.9"), VALUATION_DATE, "source-fx"),
            FxRate("USD", "EUR", Decimal("0.8"), VALUATION_DATE, "source-fx"),
        )
        with self.assertRaisesRegex(ValidationError, "Conflicting FX rates"):
            analyze_portfolio(state, prices, rates, VALUATION_DATE)

    def test_conflicting_same_date_prices_are_rejected(self) -> None:
        state, prices, fx_rates, _ = _example_inputs()
        conflicting = (*prices, replace(prices[0], amount=Decimal("101")))
        with self.assertRaisesRegex(ValidationError, "Conflicting market prices"):
            analyze_portfolio(state, conflicting, fx_rates, VALUATION_DATE)

    def test_missing_fx_is_rejected_instead_of_mixing_currencies(self) -> None:
        state = _multi_currency_state()
        prices = (
            MarketPrice("listing-eur", Decimal("100"), "EUR", VALUATION_DATE, "source-prices"),
            MarketPrice("listing-usd", Decimal("100"), "USD", VALUATION_DATE, "source-prices"),
        )
        with self.assertRaises(MissingFxRateError):
            analyze_portfolio(state, prices, (), VALUATION_DATE)

    def test_missing_price_is_rejected(self) -> None:
        state, prices, fx_rates, _ = _example_inputs()
        with self.assertRaises(MissingPriceError):
            analyze_portfolio(state, prices[:1], fx_rates, VALUATION_DATE)


class ContributionPlanningTests(unittest.TestCase):
    def test_simple_and_drift_aware_plans_are_buy_only_and_conserve_cash(self) -> None:
        state, prices, fx_rates, constraints = _example_inputs()
        original_state = deepcopy(state)
        original_prices = deepcopy(prices)
        analysis = analyze_portfolio(state, prices, fx_rates, VALUATION_DATE)

        simple = plan_contribution(
            state,
            analysis,
            prices,
            fx_rates,
            Decimal("400"),
            "EUR",
            "simple",
            VALUATION_DATE,
            constraints,
        )
        drift_aware = plan_contribution(
            state,
            analysis,
            prices,
            fx_rates,
            Decimal("400"),
            "EUR",
            "drift_aware",
            VALUATION_DATE,
            constraints,
        )

        for plan in (simple, drift_aware):
            self.assertEqual(
                plan.total_purchase_value
                + plan.total_estimated_trade_cost
                + plan.remaining_cash,
                plan.contribution_amount,
            )
            self.assertTrue(all(line.quantity >= 0 for line in plan.lines))
            self.assertLessEqual(
                plan.total_purchase_value + plan.total_estimated_trade_cost,
                Decimal("400"),
            )

        simple_drift = sum(abs(line.remaining_drift) for line in simple.lines)
        aware_drift = sum(abs(line.remaining_drift) for line in drift_aware.lines)
        self.assertLess(aware_drift, simple_drift)
        self.assertEqual(state, original_state)
        self.assertEqual(prices, original_prices)

    def test_fractional_fee_plan_matches_synthetic_eur_400_scenario(self) -> None:
        state, prices, fx_rates, constraints = _example_inputs()
        analysis = analyze_portfolio(state, prices, fx_rates, VALUATION_DATE)
        plan = plan_contribution(
            state,
            analysis,
            prices,
            fx_rates,
            Decimal("400"),
            "EUR",
            "drift_aware",
            VALUATION_DATE,
            constraints,
        )
        lines = {line.instrument_id: line for line in plan.lines}

        self.assertEqual(lines["instrument-global"].quantity, Decimal("0"))
        self.assertEqual(lines["instrument-bond"].quantity, Decimal("7.972"))
        self.assertEqual(plan.total_purchase_value, Decimal("398.600"))
        self.assertEqual(plan.total_estimated_trade_cost, Decimal("1.40"))
        self.assertEqual(plan.remaining_cash, Decimal("0.000"))

    def test_whole_share_constraints_leave_cash_without_overspending(self) -> None:
        state, prices, fx_rates, constraints = _example_inputs()
        whole_share_constraints = tuple(
            replace(constraint, fractional_allowed=False) for constraint in constraints
        )
        analysis = analyze_portfolio(state, prices, fx_rates, VALUATION_DATE)
        plan = plan_contribution(
            state,
            analysis,
            prices,
            fx_rates,
            Decimal("400"),
            "EUR",
            "simple",
            VALUATION_DATE,
            whole_share_constraints,
        )

        self.assertTrue(all(line.quantity == line.quantity.to_integral() for line in plan.lines))
        self.assertGreater(plan.remaining_cash, 0)
        self.assertEqual(
            plan.total_purchase_value
            + plan.total_estimated_trade_cost
            + plan.remaining_cash,
            Decimal("400"),
        )

    def test_whole_share_round_lot_increment_is_preserved(self) -> None:
        state, prices, fx_rates, _ = _example_inputs()
        round_lot_listing = replace(
            state.listings[0],
            fractional_allowed=False,
            quantity_increment=Decimal("10"),
        )
        round_lot_state = replace(
            state,
            listings=(round_lot_listing,) + state.listings[1:],
        )
        analysis = analyze_portfolio(
            round_lot_state, prices, fx_rates, VALUATION_DATE
        )
        plan = plan_contribution(
            round_lot_state,
            analysis,
            prices,
            fx_rates,
            Decimal("3000"),
            "EUR",
            "simple",
            VALUATION_DATE,
        )
        line = next(
            item for item in plan.lines if item.instrument_id == "instrument-global"
        )
        self.assertEqual(line.quantity, Decimal("10"))

    def test_tolerated_target_weights_are_normalized_for_budgeting(self) -> None:
        state, prices, fx_rates, _ = _example_inputs()
        target = replace(
            state.target_allocations[0],
            targets=(
                AllocationTarget("instrument-global", Decimal("0.500000004")),
                AllocationTarget("instrument-bond", Decimal("0.500000004")),
            ),
        )
        weights = {
            item.instrument_id: item.weight for item in target.targets
        }
        normalized_state = replace(
            state,
            target_allocations=(target,),
            investment_theses=tuple(
                replace(thesis, target_weight=weights[thesis.instrument_id])
                if thesis.target_weight is not None
                else thesis
                for thesis in state.investment_theses
            ),
        )
        analysis = analyze_portfolio(
            normalized_state, prices, fx_rates, VALUATION_DATE
        )
        plan = plan_contribution(
            normalized_state,
            analysis,
            prices,
            fx_rates,
            Decimal("400"),
            "EUR",
            "simple",
            VALUATION_DATE,
        )
        self.assertEqual(
            sum((line.target_weight for line in plan.lines), Decimal("0")),
            Decimal("1"),
        )
        self.assertEqual(
            plan.total_purchase_value
            + plan.total_estimated_trade_cost
            + plan.remaining_cash,
            Decimal("400"),
        )

    def test_zero_weight_target_needs_no_listing_or_market_data(self) -> None:
        state, prices, fx_rates, _ = _example_inputs()
        legacy = Instrument(
            id="instrument-zero-target",
            name="Synthetic Zero Target",
            kind="etf",
            economic_currency="EUR",
        )
        approved = replace(
            state.target_allocations[0],
            targets=(
                *state.target_allocations[0].targets,
                AllocationTarget(legacy.id, Decimal("0")),
            ),
        )
        extended = replace(
            state,
            instruments=(*state.instruments, legacy),
            target_allocations=(approved,),
        )
        analysis = analyze_portfolio(extended, prices, fx_rates, VALUATION_DATE)
        plan = plan_contribution(
            extended,
            analysis,
            prices,
            fx_rates,
            Decimal("400"),
            "EUR",
            "simple",
            VALUATION_DATE,
        )
        self.assertNotIn(legacy.id, {line.instrument_id for line in plan.lines})

    def test_cash_only_portfolio_allocates_by_target(self) -> None:
        state, prices, fx_rates, _ = _example_inputs()
        empty = replace(state, holdings=())
        analysis = analyze_portfolio(empty, prices, fx_rates, VALUATION_DATE)
        plan = plan_contribution(
            empty,
            analysis,
            prices,
            fx_rates,
            Decimal("400"),
            "EUR",
            "drift_aware",
            VALUATION_DATE,
        )

        purchases = {line.instrument_id: line.proposed_contribution for line in plan.lines}
        self.assertEqual(purchases["instrument-global"], Decimal("200.000"))
        self.assertEqual(purchases["instrument-bond"], Decimal("200.000"))

    def test_negative_contribution_is_rejected(self) -> None:
        state, prices, fx_rates, _ = _example_inputs()
        analysis = analyze_portfolio(state, prices, fx_rates, VALUATION_DATE)
        with self.assertRaisesRegex(ValidationError, "positive"):
            plan_contribution(
                state,
                analysis,
                prices,
                fx_rates,
                Decimal("-1"),
                "EUR",
                "simple",
                VALUATION_DATE,
            )

    def test_stale_or_modified_analysis_is_rejected(self) -> None:
        state, prices, fx_rates, _ = _example_inputs()
        analysis = analyze_portfolio(state, prices, fx_rates, VALUATION_DATE)
        altered = replace(analysis, total_value=Decimal("999"))
        with self.assertRaisesRegex(ValidationError, "does not match"):
            plan_contribution(
                state,
                altered,
                prices,
                fx_rates,
                Decimal("400"),
                "EUR",
                "simple",
                VALUATION_DATE,
            )

    def test_constraint_for_unknown_listing_is_rejected(self) -> None:
        state, prices, fx_rates, _ = _example_inputs()
        analysis = analyze_portfolio(state, prices, fx_rates, VALUATION_DATE)
        with self.assertRaisesRegex(ValidationError, "unknown listing"):
            plan_contribution(
                state,
                analysis,
                prices,
                fx_rates,
                Decimal("400"),
                "EUR",
                "simple",
                VALUATION_DATE,
                (TradingConstraint(listing_id="missing-listing"),),
            )

    def test_small_and_large_contributions_preserve_cash(self) -> None:
        state, prices, fx_rates, constraints = _example_inputs()
        analysis = analyze_portfolio(state, prices, fx_rates, VALUATION_DATE)
        for amount in (Decimal("5"), Decimal("10000")):
            with self.subTest(amount=amount):
                plan = plan_contribution(
                    state,
                    analysis,
                    prices,
                    fx_rates,
                    amount,
                    "EUR",
                    "simple",
                    VALUATION_DATE,
                    constraints,
                )
                self.assertEqual(
                    plan.total_purchase_value
                    + plan.total_estimated_trade_cost
                    + plan.remaining_cash,
                    amount,
                )
                self.assertGreaterEqual(plan.remaining_cash, 0)
        small = plan_contribution(
            state,
            analysis,
            prices,
            fx_rates,
            Decimal("5"),
            "EUR",
            "simple",
            VALUATION_DATE,
            constraints,
        )
        self.assertEqual(small.total_purchase_value, 0)
        self.assertEqual(small.remaining_cash, Decimal("5"))

    def test_contribution_id_covers_plan_defining_inputs(self) -> None:
        state, prices, fx_rates, constraints = _example_inputs()
        analysis = analyze_portfolio(state, prices, fx_rates, VALUATION_DATE)

        baseline = plan_contribution(
            state,
            analysis,
            prices,
            fx_rates,
            Decimal("400"),
            "EUR",
            "simple",
            VALUATION_DATE,
            constraints,
        )
        repeated = plan_contribution(
            state,
            analysis,
            prices,
            fx_rates,
            Decimal("400"),
            "EUR",
            "simple",
            VALUATION_DATE,
            tuple(reversed(constraints)),
        )
        changed_amount = plan_contribution(
            state,
            analysis,
            prices,
            fx_rates,
            Decimal("401"),
            "EUR",
            "simple",
            VALUATION_DATE,
            constraints,
        )
        changed_prices = tuple(
            replace(price, amount=price.amount + Decimal("1"))
            if price.listing_id == "listing-global-xetr"
            else price
            for price in prices
        )
        changed_analysis = analyze_portfolio(
            state, changed_prices, fx_rates, VALUATION_DATE
        )
        changed_market = plan_contribution(
            state,
            changed_analysis,
            changed_prices,
            fx_rates,
            Decimal("400"),
            "EUR",
            "simple",
            VALUATION_DATE,
            constraints,
        )
        changed_listings = tuple(
            replace(listing, quantity_increment=Decimal("3"))
            if listing.id == "listing-global-xetr"
            else listing
            for listing in state.listings
        )
        changed_listing_state = replace(state, listings=changed_listings)
        changed_listing_analysis = analyze_portfolio(
            changed_listing_state, prices, fx_rates, VALUATION_DATE
        )
        baseline_without_overrides = plan_contribution(
            state,
            analysis,
            prices,
            fx_rates,
            Decimal("400"),
            "EUR",
            "simple",
            VALUATION_DATE,
        )
        changed_listing_plan = plan_contribution(
            changed_listing_state,
            changed_listing_analysis,
            prices,
            fx_rates,
            Decimal("400"),
            "EUR",
            "simple",
            VALUATION_DATE,
        )

        self.assertEqual(baseline.id, repeated.id)
        self.assertNotEqual(baseline.id, changed_amount.id)
        self.assertNotEqual(baseline.id, changed_market.id)
        self.assertNotEqual(
            baseline_without_overrides.id, changed_listing_plan.id
        )
        self.assertNotEqual(
            baseline_without_overrides.lines[0].quantity,
            changed_listing_plan.lines[0].quantity,
        )


class StorageAndReportingTests(unittest.TestCase):
    def test_workspace_root_symlink_is_rejected(self) -> None:
        state, _, _, _ = _example_inputs()
        with tempfile.TemporaryDirectory(prefix="steadyfolio-symlink-test-") as temporary:
            base = Path(temporary)
            actual_workspace = base / "actual-workspace"
            workspace_link = base / "workspace-link"
            actual_workspace.mkdir()
            try:
                os.symlink(actual_workspace, workspace_link, target_is_directory=True)
            except OSError as error:
                self.skipTest(f"Directory symlinks are unavailable: {error}")
            with self.assertRaises(StorageSafetyError):
                initialize_workspace(workspace_link, state)

    def test_private_state_initialization_is_atomic_and_non_overwriting(self) -> None:
        state, _, _, _ = _example_inputs()
        with tempfile.TemporaryDirectory(prefix="steadyfolio-workspace-") as temporary:
            workspace = Path(temporary)
            state_path = initialize_workspace(workspace, state)
            original = state_path.read_bytes()

            self.assertEqual(load_state(workspace), state)
            with self.assertRaises(FileExistsError):
                initialize_workspace(workspace, replace(state, holdings=()))
            self.assertEqual(state_path.read_bytes(), original)

            invalid = replace(state, schema_version="unsupported")
            with self.assertRaises(ValidationError):
                save_state(workspace, invalid, overwrite=True)
            self.assertEqual(state_path.read_bytes(), original)

    def test_overwrite_cannot_rewrite_an_approved_allocation_version(self) -> None:
        state, _, _, _ = _example_inputs()
        changed_target = replace(
            state.target_allocations[0], rationale="Changed after approval"
        )
        changed_state = replace(state, target_allocations=(changed_target,))
        with tempfile.TemporaryDirectory(prefix="steadyfolio-workspace-") as temporary:
            workspace = Path(temporary)
            state_path = initialize_workspace(workspace, state)
            original = state_path.read_bytes()
            with self.assertRaisesRegex(ValidationError, "immutable"):
                save_state(workspace, changed_state, overwrite=True)
            self.assertEqual(state_path.read_bytes(), original)

    def test_invalid_derived_results_are_rejected_before_persistence(self) -> None:
        state, prices, fx_rates, constraints = _example_inputs()
        analysis = analyze_portfolio(state, prices, fx_rates, VALUATION_DATE)
        plan = plan_contribution(
            state,
            analysis,
            prices,
            fx_rates,
            Decimal("400"),
            "EUR",
            "drift_aware",
            VALUATION_DATE,
            constraints,
        )
        with tempfile.TemporaryDirectory(prefix="steadyfolio-workspace-") as temporary:
            with self.assertRaisesRegex(ValidationError, "finite"):
                save_analysis_result(
                    temporary,
                    replace(analysis, total_value=Decimal("NaN")),
                )
            with self.assertRaisesRegex(ValidationError, "reconcile"):
                save_contribution_plan(
                    temporary,
                    replace(plan, remaining_cash=plan.remaining_cash + Decimal("1")),
                )

    def test_private_output_rejects_path_traversal(self) -> None:
        state, prices, fx_rates, _ = _example_inputs()
        analysis = analyze_portfolio(state, prices, fx_rates, VALUATION_DATE)
        with tempfile.TemporaryDirectory(prefix="steadyfolio-workspace-") as temporary:
            with self.assertRaises(StorageSafetyError):
                save_analysis_result(temporary, analysis, filename="../public.json")

    def test_private_results_and_reports_are_written_below_private(self) -> None:
        state, prices, fx_rates, constraints = _example_inputs()
        analysis = analyze_portfolio(state, prices, fx_rates, VALUATION_DATE)
        plan = plan_contribution(
            state,
            analysis,
            prices,
            fx_rates,
            Decimal("400"),
            "EUR",
            "drift_aware",
            VALUATION_DATE,
            constraints,
        )
        report = render_contribution_report(state, analysis, plan)
        with tempfile.TemporaryDirectory(prefix="steadyfolio-workspace-") as temporary:
            result_path = save_analysis_result(temporary, analysis)
            plan_path = save_contribution_plan(temporary, plan)
            report_path = save_report(temporary, report)

            private = (Path(temporary) / "private").resolve()
            for output in (result_path, plan_path, report_path):
                self.assertTrue(output.resolve().is_relative_to(private))
                self.assertTrue(output.is_file())

    def test_private_root_symlink_is_rejected(self) -> None:
        state, _, _, _ = _example_inputs()
        with tempfile.TemporaryDirectory(prefix="steadyfolio-symlink-test-") as temporary:
            base = Path(temporary)
            workspace = base / "workspace"
            outside = base / "outside"
            workspace.mkdir()
            outside.mkdir()
            try:
                os.symlink(outside, workspace / "private", target_is_directory=True)
            except OSError as error:
                self.skipTest(f"Directory symlinks are unavailable: {error}")
            with self.assertRaises(StorageSafetyError):
                initialize_workspace(workspace, state)

    def test_private_output_directory_symlink_is_rejected(self) -> None:
        state, prices, fx_rates, _ = _example_inputs()
        analysis = analyze_portfolio(state, prices, fx_rates, VALUATION_DATE)
        with tempfile.TemporaryDirectory(prefix="steadyfolio-symlink-test-") as temporary:
            base = Path(temporary)
            workspace = base / "workspace"
            outside = base / "outside"
            (workspace / "private").mkdir(parents=True)
            outside.mkdir()
            try:
                os.symlink(
                    outside,
                    workspace / "private" / "results",
                    target_is_directory=True,
                )
            except OSError as error:
                self.skipTest(f"Directory symlinks are unavailable: {error}")
            with self.assertRaises(StorageSafetyError):
                save_analysis_result(workspace, analysis)

    def test_dangling_private_output_file_symlink_is_rejected(self) -> None:
        state, prices, fx_rates, _ = _example_inputs()
        analysis = analyze_portfolio(state, prices, fx_rates, VALUATION_DATE)
        with tempfile.TemporaryDirectory(prefix="steadyfolio-symlink-test-") as temporary:
            base = Path(temporary)
            workspace = base / "workspace"
            results = workspace / "private" / "results"
            outside = base / "outside.json"
            results.mkdir(parents=True)
            try:
                os.symlink(outside, results / "analysis.json")
            except OSError as error:
                self.skipTest(f"File symlinks are unavailable: {error}")
            with self.assertRaises(StorageSafetyError):
                save_analysis_result(workspace, analysis)

    def test_loading_missing_state_does_not_create_private_directories(self) -> None:
        with tempfile.TemporaryDirectory(prefix="steadyfolio-workspace-") as temporary:
            workspace = Path(temporary)
            with self.assertRaises(FileNotFoundError):
                load_state(workspace)
            self.assertFalse((workspace / "private").exists())

    def test_report_is_english_structured_and_reconciled(self) -> None:
        state, prices, fx_rates, constraints = _example_inputs()
        analysis = analyze_portfolio(state, prices, fx_rates, VALUATION_DATE)
        plan = plan_contribution(
            state,
            analysis,
            prices,
            fx_rates,
            Decimal("400"),
            "EUR",
            "drift_aware",
            VALUATION_DATE,
            constraints,
        )
        report = render_contribution_report(state, analysis, plan)

        self.assertIn("# Monthly Contribution Plan", report)
        self.assertIn("Available contribution: 400.00 EUR", report)
        self.assertIn("No sale or executed transaction", report)
        self.assertIn("not a forecast or financial advice", report)

    def test_report_uses_neutral_provenance_and_escapes_table_names(self) -> None:
        state, prices, fx_rates, constraints = _example_inputs()
        renamed = replace(state.instruments[0], name="Synthetic | Equity\nETF")
        changed_state = replace(
            state, instruments=(renamed,) + state.instruments[1:]
        )
        analysis = analyze_portfolio(
            changed_state, prices, fx_rates, VALUATION_DATE
        )
        plan = plan_contribution(
            changed_state,
            analysis,
            prices,
            fx_rates,
            Decimal("400"),
            "EUR",
            "drift_aware",
            VALUATION_DATE,
            constraints,
        )
        reports = (
            render_analysis_report(changed_state, analysis),
            render_contribution_report(changed_state, analysis, plan),
        )
        for report in reports:
            with self.subTest(report=report.splitlines()[0]):
                self.assertIn("Synthetic \\| Equity ETF", report)
                self.assertNotIn("synthetic assumptions", report)

    def test_structured_outputs_match_schema_required_fields(self) -> None:
        state, prices, fx_rates, constraints = _example_inputs()
        analysis = analyze_portfolio(state, prices, fx_rates, VALUATION_DATE)
        plan = plan_contribution(
            state,
            analysis,
            prices,
            fx_rates,
            Decimal("400"),
            "EUR",
            "drift_aware",
            VALUATION_DATE,
            constraints,
        )
        for schema_name, value in (
            ("analysis-result.schema.json", analysis),
            ("contribution-plan.schema.json", plan),
        ):
            with self.subTest(schema=schema_name):
                schema = _read_json(REPOSITORY_ROOT / "schemas" / schema_name)
                self.assertEqual(set(schema["required"]), set(to_json_value(value)))


if __name__ == "__main__":
    unittest.main()
