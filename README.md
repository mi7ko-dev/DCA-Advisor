# SteadyFolio

SteadyFolio is a local-first, deterministic portfolio-maintenance core for
contribution-based investors. The Phase 3 MVP values a portfolio, reports current
weights and signed drift, and produces buy-only simple or drift-aware contribution
plans under explicit price, FX, fee, minimum-trade, and share-increment assumptions.

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
```

The inputs are `examples/portfolio.example.json`,
`examples/market-input.example.json`, and
`examples/contribution-request.example.json`. Generated output remains synthetic
and is written only below `examples/results/` and `examples/reports/`.

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

SteadyFolio is provided under the MIT License. It is not financial advice.
