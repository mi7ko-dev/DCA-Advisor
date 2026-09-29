# SteadyFolio

SteadyFolio is a local-first, deterministic portfolio-maintenance core and
repository-local conversational skill for contribution-based investors. It values
a portfolio, reports current weights and signed drift, produces buy-only simple or
drift-aware contribution plans, adds coverage-aware portfolio intelligence, and
routes bounded review workflows over structured results. It also supports offline,
evidence-limited individual-equity quality and valuation review plus explicit
portfolio-policy checks.

The project does not place orders, connect to brokers, provide tax or suitability
advice, forecast returns, or infer missing market data. All tracked examples are
fully synthetic.

## Runtime

- Python 3.11 or newer.
- No runtime dependencies outside the Python standard library.
- Decimal strings are used for persisted financial values; calculations use
  `decimal.Decimal`.

## Quick start

Create an isolated Python 3.11 environment and install the deterministic core from
the repository:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install --no-deps .
.venv\Scripts\python -c "import steadyfolio; assert callable(steadyfolio.run_committee_workflow)"
```

For Codex, either open this repository and invoke the discovered repo-local skill
with `$steadyfolio`, or install the reproducible local plugin marketplace:

```powershell
codex plugin marketplace add .
codex plugin add steadyfolio@steadyfolio-local
```

Start a new Codex thread after installation. No credential or environment variable
is required by the implemented offline version. See `docs/OPERATIONS.md` for the
synthetic walkthrough, private initialization, provider flow, and troubleshooting.

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
python tools/generate_synthetic_equity.py
python tools/generate_synthetic_multi_agent.py
```

The inputs are `examples/portfolio.example.json`,
`examples/market-input.example.json`, and
`examples/contribution-request.example.json` for Phase 3, plus
`examples/research-snapshot.example.json`, `examples/stress-windows.example.json`,
and `examples/thesis-evidence.example.json` for Phase 4. Generated output remains
synthetic. Phase 7 adds the synthetic equity evidence and portfolio-policy examples.
Generated Phase 3 through Phase 5 output is written below `examples/results/` and
`examples/reports/`; the paired Phase 7 examples are kept directly under
`examples/`.
After regeneration, `git diff --exit-code -- examples` must succeed.

## Conversational skill

The canonical repo-local skill is at
`.agents/skills/steadyfolio/SKILL.md`. It routes monthly contributions, portfolio
reviews, ETF thesis checks, and overlap questions through the deterministic engine.
It also routes individual-stock review when dated structured equity evidence is
supplied.
Routine contributions do not invoke research or agents. Portfolio, overlap, and
thesis routes retain their disclosed sequential review lenses. Phase 8 equity
review uses four separate Codex-native specialist threads and one critic thread
when host subagents are available, with one execution per role and no retries or
live market-data calls. If the host cannot spawn subagents, the result is labeled
as a deterministic-only fallback rather than multi-agent.

The six synthetic end-to-end demonstrations are in
`examples/results/committee-workflows.example.json` and
`examples/reports/committee-workflows.md`. The output separates calculations,
sources and dates, limitations, assumptions, interpretations, disagreements, and
next actions while identifying the tools and lenses actually used. Review lenses
are not presented as independent agents or verification.

The synthetic Phase 8 contract demonstration and defect-based eval are in
`examples/results/multi-agent-equity-review.example.json`,
`examples/results/multi-agent-eval.example.json`, and
`examples/reports/multi-agent-equity-review.md`. Their runtime is explicitly
`in_memory_test_backend`; they test contracts and bounds rather than claiming live
model execution.

## Portfolio intelligence

The project includes a replaceable provider protocol and an offline synthetic
provider. It supports sourced fund facts, partial holdings overlap, observed
company/issuer concentration, sector/geography/currency exposure, historical return/volatility/
drawdown/correlation, benchmark and stress comparisons, and non-mutating thesis
review.

Coverage and freshness are part of every result. Missing holdings or exposure data
is reported as unclassified, not converted to zero. Company exposure is aggregated
by stable issuer ID across direct and look-through holdings. Historical inputs must
contain enough observations and use compatible periods, currencies, return
conventions, distribution treatment, and corporate-action treatment.

No live data provider is included. Provider interfaces and exact methodology are
documented in `docs/RESEARCH.md`.

## Individual-equity review

The offline equity route validates ISIN, instrument name, and optional listing
identity before scoring. It keeps business quality, circle of competence,
valuation, and owner-earnings interpretation separate. Missing criteria remain
unavailable rather than becoming zero, and conflicting valuation methods are not
averaged.

Portfolio-policy thresholds and classifications are explicit data rather than
global constants. Real policy instances belong under `private/`. The current
policy denominator is invested positions and therefore excludes unmodelled cash.
See `docs/EQUITY_REVIEW.md` for the contracts and limitations.

Codex-native equity specialists receive role-minimal immutable packets. These
packets are processed by the selected Codex model service, so a real run adds token
use, latency, and hosted processing compared with the deterministic-only path. No
request or account ID, source path, raw provider payload, or free-form portfolio
note is included; portfolio risk receives typed aggregates only. Execution metadata
comes from the host, not model self-report. No API key or third-party Python
dependency is added to SteadyFolio.

## Private workspace boundary

Real user state and every output derived from it belong under an explicitly chosen
workspace root's ignored `private/` directory. The Python storage API validates the
complete state before writing, uses an atomic same-filesystem operation, refuses to
overwrite by default, and rejects unsafe output names and symlink escapes.

The initialization example and maintenance rules are in `docs/OPERATIONS.md`.
Private source material must already be below the selected `private/` root or live
outside the public repository. Do not place real state in `examples/`, `tests/`, or
beside the installed package.

## Calculation contract

The exact valuation, drift, DCA, fee, residual-cash, and concentration conventions
are documented in `docs/CALCULATIONS.md`. Architecture and privacy boundaries are
documented in `docs/ARCHITECTURE.md` and `docs/SECURITY.md`.
Portfolio-intelligence methodology is documented in `docs/RESEARCH.md`.
Conversational routing, approval gates, host status, and limitations are documented
in `docs/COMMITTEE.md`. Operational setup is in `docs/OPERATIONS.md`, and the narrow
change, verification, distribution, and license process is in
`docs/MAINTENANCE.md`.

The repository contains the source package, repo-local skill, and a reproducible
Codex marketplace manifest at `.agents/plugins/marketplace.json` whose plugin is at
`plugins/steadyfolio/`. `tools/build_plugin.py` assembles the self-contained plugin
only from an explicit public allowlist and CI compares a clean temporary build
byte-for-byte with the tracked package. No release archive is published;
publication still requires separate authorization.

SteadyFolio is provided under the MIT License. It is not financial advice.
