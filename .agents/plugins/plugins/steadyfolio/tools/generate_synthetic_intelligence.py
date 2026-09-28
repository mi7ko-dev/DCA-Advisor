"""Regenerate deterministic Phase 4 examples from public synthetic inputs."""

from __future__ import annotations

import json
from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from steadyfolio.calculations import analyze_portfolio  # noqa: E402
from steadyfolio.intelligence import analyze_portfolio_intelligence  # noqa: E402
from steadyfolio.intelligence_reporting import (  # noqa: E402
    render_intelligence_report,
    render_thesis_review_report,
)
from steadyfolio.models import to_json_value  # noqa: E402
from steadyfolio.providers import StaticResearchProvider  # noqa: E402
from steadyfolio.research_models import ResearchRequest  # noqa: E402
from steadyfolio.research_validation import (  # noqa: E402
    research_snapshot_from_dict,
    stress_windows_from_dict,
    thesis_evidence_from_dict,
)
from steadyfolio.thesis import review_investment_thesis  # noqa: E402
from steadyfolio.validation import (  # noqa: E402
    fx_rates_from_dict,
    market_prices_from_dict,
    state_from_dict,
)


EXAMPLES = REPOSITORY_ROOT / "examples"
ANALYSIS_DATE = "2026-01-31"


def _read(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=True, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
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
    provider = StaticResearchProvider(
        "SteadyFolio Synthetic Research Provider", snapshot
    )
    supplied = provider.fetch(
        ResearchRequest(
            instrument_ids=tuple(item.id for item in state.instruments),
            listing_ids=tuple(item.id for item in state.listings),
            as_of=ANALYSIS_DATE,
        )
    )
    stress_windows = stress_windows_from_dict(
        _read(EXAMPLES / "stress-windows.example.json")
    )
    intelligence = analyze_portfolio_intelligence(
        state, analysis, supplied, ANALYSIS_DATE, stress_windows
    )

    thesis_input = _read(EXAMPLES / "thesis-evidence.example.json")
    thesis_review = review_investment_thesis(
        state,
        thesis_input["thesis_id"],
        thesis_evidence_from_dict(thesis_input["evidence"]),
        thesis_input["observed_review_triggers"],
        thesis_input["reviewed_at"],
        supplied,
    )

    _write_json(
        EXAMPLES / "results" / "intelligence.example.json",
        to_json_value(intelligence),
    )
    _write_json(
        EXAMPLES / "results" / "thesis-review.example.json",
        to_json_value(thesis_review),
    )
    (EXAMPLES / "reports" / "portfolio-intelligence.md").write_text(
        render_intelligence_report(state, intelligence), encoding="utf-8"
    )
    (EXAMPLES / "reports" / "thesis-review.md").write_text(
        render_thesis_review_report(state, thesis_review), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
