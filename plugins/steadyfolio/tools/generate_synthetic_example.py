#!/usr/bin/env python3
"""Regenerate tracked outputs from the fully synthetic Phase 3 inputs."""

from __future__ import annotations

from decimal import Decimal
import json
from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from steadyfolio.calculations import analyze_portfolio, plan_contribution  # noqa: E402
from steadyfolio.models import to_json_value  # noqa: E402
from steadyfolio.reporting import render_contribution_report  # noqa: E402
from steadyfolio.validation import (  # noqa: E402
    constraints_from_dict,
    fx_rates_from_dict,
    market_prices_from_dict,
    state_from_dict,
)


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=True, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    examples = REPOSITORY_ROOT / "examples"
    state = state_from_dict(_read_json(examples / "portfolio.example.json"))
    market = _read_json(examples / "market-input.example.json")
    request = _read_json(examples / "contribution-request.example.json")
    prices = market_prices_from_dict(market["prices"])
    fx_rates = fx_rates_from_dict(market["fx_rates"])
    constraints = constraints_from_dict(request["constraints"])

    analysis = analyze_portfolio(
        state, prices, fx_rates, request["valuation_date"]
    )
    plan = plan_contribution(
        state=state,
        analysis=analysis,
        prices=prices,
        fx_rates=fx_rates,
        contribution_amount=Decimal(request["contribution_amount"]),
        currency=request["currency"],
        method=request["method"],
        valuation_date=request["valuation_date"],
        constraints=constraints,
        preferred_listings=request["preferred_listings"],
    )

    _write_json(examples / "results" / "analysis.example.json", to_json_value(analysis))
    _write_json(
        examples / "results" / "contribution-plan.example.json",
        to_json_value(plan),
    )
    report = render_contribution_report(state, analysis, plan)
    report_path = examples / "reports" / "monthly-contribution.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report.rstrip() + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
