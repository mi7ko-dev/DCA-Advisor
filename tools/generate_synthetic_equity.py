#!/usr/bin/env python3
"""Generate deterministic Phase 7 equity and policy examples."""

from __future__ import annotations

import json
from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from steadyfolio.calculations import analyze_portfolio  # noqa: E402
from steadyfolio.equity import review_equity  # noqa: E402
from steadyfolio.equity_reporting import (  # noqa: E402
    render_equity_review_report,
    render_portfolio_policy_report,
)
from steadyfolio.equity_validation import equity_review_input_from_dict  # noqa: E402
from steadyfolio.models import to_json_value  # noqa: E402
from steadyfolio.portfolio_policy import (  # noqa: E402
    evaluate_portfolio_policy,
    portfolio_policy_from_dict,
)
from steadyfolio.validation import (  # noqa: E402
    fx_rates_from_dict,
    market_prices_from_dict,
    state_from_dict,
)


EXAMPLES = REPOSITORY_ROOT / "examples"


def _read(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=True, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    equity_state = state_from_dict(_read(EXAMPLES / "equity-portfolio.example.json"))
    equity_input = equity_review_input_from_dict(
        _read(EXAMPLES / "equity-evidence.example.json")
    )
    equity_result = review_equity(equity_state, equity_input)
    _write_json(
        EXAMPLES / "equity-review.example.json",
        to_json_value(equity_result),
    )
    (EXAMPLES / "equity-review.example.md").write_text(
        render_equity_review_report(equity_result) + "\n",
        encoding="utf-8",
    )

    portfolio_state = state_from_dict(_read(EXAMPLES / "portfolio.example.json"))
    market = _read(EXAMPLES / "market-input.example.json")
    analysis = analyze_portfolio(
        portfolio_state,
        market_prices_from_dict(market["prices"]),
        fx_rates_from_dict(market["fx_rates"]),
        "2026-01-31",
    )
    policy = portfolio_policy_from_dict(
        _read(EXAMPLES / "portfolio-policy.example.json")
    )
    policy_result = evaluate_portfolio_policy(portfolio_state, analysis, policy)
    _write_json(
        EXAMPLES / "portfolio-policy-result.example.json",
        to_json_value(policy_result),
    )
    (EXAMPLES / "portfolio-policy-result.example.md").write_text(
        render_portfolio_policy_report(policy_result) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
