#!/usr/bin/env python3
"""Generate Phase 5 committee examples from fully synthetic public inputs."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from steadyfolio.committee import (  # noqa: E402
    committee_request_from_message,
    run_committee_workflow,
)
from steadyfolio.committee_reporting import render_committee_report  # noqa: E402
from steadyfolio.models import to_json_value  # noqa: E402
from steadyfolio.providers import StaticResearchProvider  # noqa: E402
from steadyfolio.research_validation import (  # noqa: E402
    research_snapshot_from_dict,
    stress_windows_from_dict,
    thesis_evidence_from_dict,
)
from steadyfolio.validation import (  # noqa: E402
    constraints_from_dict,
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
    state = state_from_dict(_read(EXAMPLES / "portfolio.example.json"))
    market = _read(EXAMPLES / "market-input.example.json")
    contribution = _read(EXAMPLES / "contribution-request.example.json")
    snapshot = research_snapshot_from_dict(
        _read(EXAMPLES / "research-snapshot.example.json")
    )
    stress_windows = stress_windows_from_dict(
        _read(EXAMPLES / "stress-windows.example.json")
    )
    thesis_raw = _read(EXAMPLES / "thesis-evidence.example.json")
    thesis_evidence = thesis_evidence_from_dict(thesis_raw["evidence"])
    requests = _read(EXAMPLES / "committee-requests.example.json")["requests"]

    prices = market_prices_from_dict(market["prices"])
    fx_rates = fx_rates_from_dict(market["fx_rates"])
    constraints = constraints_from_dict(contribution["constraints"])
    results = []
    reports = []
    for raw in requests:
        request = committee_request_from_message(
            raw["id"],
            raw["message"],
            raw["as_of"],
            instrument_id=raw.get("instrument_id"),
            thesis_id=raw.get("thesis_id"),
        )
        selected_snapshot = snapshot
        if raw["scenario"] == "missing_stale_research":
            selected_snapshot = replace(
                snapshot,
                fund_holdings=(),
                classified_exposures=(),
                historical_series=(),
            )
        result = run_committee_workflow(
            request,
            state,
            prices,
            fx_rates,
            constraints,
            research_provider=StaticResearchProvider(
                "SteadyFolio Synthetic Research Provider", selected_snapshot
            ),
            stress_windows=stress_windows,
            thesis_evidence=thesis_evidence if raw["id"] == "demo-etf-thesis" else (),
            observed_review_triggers=(
                thesis_raw["observed_review_triggers"]
                if raw["id"] == "demo-etf-thesis"
                else ()
            ),
        )
        results.append(to_json_value(result))
        reports.append(
            render_committee_report(
                result,
                title=f"Synthetic Committee Demo: {raw['id']}",
            )
        )

    _write_json(
        EXAMPLES / "results" / "committee-workflows.example.json",
        {"synthetic": True, "scenarios": results},
    )
    (EXAMPLES / "reports" / "committee-workflows.md").write_text(
        "\n\n---\n\n".join(reports).rstrip() + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
