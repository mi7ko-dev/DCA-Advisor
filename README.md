# SteadyFolio

SteadyFolio is a local-first, deterministic portfolio-maintenance core and
repository-local conversational skill for contribution-based investors. It values
a portfolio, reports current weights and signed drift, produces buy-only simple or
drift-aware contribution plans, adds coverage-aware portfolio intelligence, and
routes bounded review workflows over structured results.

The project does not place orders, connect to brokers, provide tax or suitability
advice, forecast returns, or infer missing market data. All tracked examples are
fully synthetic.

## Runtime

- Python 3.11 or newer.
- No runtime dependencies outside the Python standard library.
- Decimal strings are used for persisted financial values; calculations use
  `decimal.Decimal`.

## Run the checks

```powershell
python -m unittest discover -s tests -p "test_*.py"
python tools/run_repository_checks.py --require-gitleaks
```

Regenerate the public synthetic result and English report:

```powershell
python tools/generate_synthetic_example.py
python tools/generate_synthetic_intelligence.py
python tools/generate_synthetic_committee.py
```

The inputs are `examples/portfolio.example.json`,
`examples/market-input.example.json`, and
`examples/contribution-request.example.json` for Phase 3, plus
`examples/research-snapshot.example.json`, `examples/stress-windows.example.json`,
and `examples/thesis-evidence.example.json` for Phase 4. Generated output remains
synthetic and is written only below `examples/results/` and `examples/reports/`.

## Conversational skill

Phase 5 adds the canonical repo-local skill at
`.agents/skills/steadyfolio/SKILL.md`. It routes monthly contributions, portfolio
reviews, ETF thesis checks, and overlap questions through the deterministic engine.
Routine contributions do not invoke research or a committee. Evidence-dependent
reviews use only relevant sequential review lenses, at most one critic pass, and no
live external calls.

The six synthetic end-to-end demonstrations are in
`examples/results/committee-workflows.example.json` and
`examples/reports/committee-workflows.md`. The output separates calculations,
sources and dates, limitations, assumptions, interpretations, disagreements, and
next actions while identifying the tools and lenses actually used. Review lenses
are not presented as independent agents or verification.

## Portfolio intelligence

Phase 4 adds a replaceable provider protocol and an offline synthetic provider. It
supports sourced fund facts, partial holdings overlap, observed company/issuer
concentration, sector/geography/currency exposure, historical return/volatility/
drawdown/correlation, benchmark and stress comparisons, and non-mutating thesis
review.

Coverage and freshness are part of every result. Missing holdings or exposure data
is reported as unclassified, not converted to zero. Historical inputs must use
compatible periods, currencies, return conventions, distribution treatment, and
corporate-action treatment.

No live data provider is included. Provider interfaces and exact methodology are
documented in `docs/RESEARCH.md`.

## Private workspace boundary

Real user state and every output derived from it belong under an explicitly chosen
workspace root's ignored `private/` directory. The Python storage API validates the
complete state before writing, uses an atomic same-filesystem operation, refuses to
overwrite by default, and rejects unsafe output names and symlink escapes.

```python
from pathlib import Path
import json

from steadyfolio.storage import initialize_workspace
from steadyfolio.validation import state_from_dict

workspace = Path("an-explicit-workspace-root")
state = state_from_dict(json.loads(Path("input.json").read_text(encoding="utf-8")))
initialize_workspace(workspace, state)
```

The example assumes the package is installed from this repository or `src/` is on
`PYTHONPATH`. Do not place real state in `examples/`, `tests/`, or beside the
installed package.

## Calculation contract

The exact valuation, drift, DCA, fee, residual-cash, and concentration conventions
are documented in `docs/CALCULATIONS.md`. Architecture and privacy boundaries are
documented in `docs/ARCHITECTURE.md` and `docs/SECURITY.md`.
Portfolio-intelligence methodology is documented in `docs/RESEARCH.md`.
Conversational routing, approval gates, host status, and limitations are documented
in `docs/COMMITTEE.md`.

SteadyFolio is provided under the MIT License. It is not financial advice.
