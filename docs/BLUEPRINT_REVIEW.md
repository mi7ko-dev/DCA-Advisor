# Blueprint Review

## Scope and evidence

This Phase 1 review evaluates the six read-only reference repositories recorded in
`blueprint/BLUEPRINT_SOURCES.md`. It is an implementation audit, not a product
architecture decision. The review focuses on the parts that could inform a small
conversational portfolio-maintenance skill for long-term, contribution-based
investing.

All six recorded commits were re-verified locally and their worktrees were clean.
The conclusions below are based on static source, test, documentation, dependency,
and license inspection at those commits. No upstream dependency was installed and
no upstream script or test suite was executed. Test files therefore show intended
coverage, not locally reproduced results.

| Reference | Audited commit | License observed at that commit | Evidence level |
| --- | --- | --- | --- |
| CoFolio | `ffb3203075267a7b4093c4d2aa49449d9357d188` | MIT | Source, instructions, dependency metadata, and license inspected |
| FinRobot | `6d6ccd32c1b8b1904dc656cf06897438aba3daec` | Apache-2.0 plus `NOTICE` | Selected source, tests, dependencies, license, and notice inspected |
| AI Finance Assistant (Finnie) | `c835596ba86c5d1f85f079776a113184073f9e71` | Source viewing only; no general reuse grant | Architecture, guards, state, tests, dependencies, and license inspected |
| Wealthfolio | `857e69a96f39d5b96db6bc5c8ce6c9086fb7b03c` | AGPL-3.0 at root; MIT for `packages/addon-sdk` | Selected domain models, algorithms, tests, docs, and licenses inspected |
| Ghostfolio | `af3d72f94c61d0d0380798f21567de70e4d4adc6` | AGPL-3.0 | Selected schema, portfolio models, calculations, tests, and license inspected |
| PyPortfolioOpt | `a6638d2e06dae6f444fd022cfd4b3c528902a85b` | MIT | Library source, tests, dependencies, docs, and license inspected |

License observations are engineering constraints, not legal advice. Public source
availability alone is not treated as permission to copy.

## Executive findings

- CoFolio is the closest product-shape reference: one skill, staged instructions,
  deterministic helper scripts, and a portfolio-maintenance workflow. Its storage
  locations, informal schemas, validation, market-data handling, and lack of tests
  make it unsuitable for use unchanged.
- FinRobot and Finnie demonstrate useful orchestration boundaries: specialists
  receive structured inputs, tool loops are bounded, and a synthesizer combines
  outputs. Their frameworks, external-service surface, caches, traces, and server
  infrastructure are unnecessary for the initial SteadyFolio scope.
- Wealthfolio has the strongest inspected accounting and instrument model. Exact
  decimals, listings identified with exchange MICs, dated FX contexts, tax lots,
  provider provenance, drift, and whole-share rebalancing are valuable design
  references. The main codebase is AGPL-3.0 and far larger than a skill needs.
- Ghostfolio provides mature buy-and-hold concepts, import validation, performance
  reporting, benchmarks, and concentration rules. It is a hosted application with
  authentication and database infrastructure, uses AGPL-3.0, and is not a suitable
  foundation for this project.
- PyPortfolioOpt is a well-tested optimization library, but mean-variance and
  related optimizers solve a different, more assumption-heavy problem than a
  transparent EUR 300-500 contribution allocator. Its core dependency set is not
  justified for the MVP.
- The most promising direction for Phase 2 is a clean, small implementation that
  adopts concepts rather than an upstream application: CoFolio's staged workflow,
  Wealthfolio's domain separations and decimal discipline, and limited
  role/tool/synthesis patterns from FinRobot and Finnie.

## CoFolio

### Verified capabilities and useful concepts

CoFolio implements a single portfolio-advisor skill with a staged workflow. The
skill dispatches to focused instruction files for investor profile, allocation,
research, construction, review, reporting, and maintenance. It uses files as the
handoff between stages and separates narrative decisions from small Python
calculators.

Relevant paths:

- `plugins/cofolio/skills/portfolio-advisor/SKILL.md`
- `plugins/cofolio/skills/portfolio-advisor/references/1-investor-profile.md`
- `plugins/cofolio/skills/portfolio-advisor/references/2-asset-allocation.md`
- `plugins/cofolio/skills/portfolio-advisor/references/3-macro-research.md`
- `plugins/cofolio/skills/portfolio-advisor/references/4-security-selection.md`
- `plugins/cofolio/skills/portfolio-advisor/references/5-portfolio-construction.md`
- `plugins/cofolio/skills/portfolio-advisor/references/6-report-generation.md`
- `plugins/cofolio/skills/portfolio-advisor/references/7-maintenance.md`
- `plugins/cofolio/skills/portfolio-advisor/references/macro-researcher.md`
- `plugins/cofolio/skills/portfolio-advisor/references/security-screener.md`
- `plugins/cofolio/skills/portfolio-advisor/scripts/{dca,drift,rebalance,overlap,concentration,fees,prices}.py`

Useful SteadyFolio concepts are progressive disclosure, invoking only the relevant
stage, keeping arithmetic in deterministic tools, recording data freshness, and
preferring contribution-based rebalancing before sales.

### Calculation and test quality

- `dca.py` deterministically allocates a contribution by target weights, but does
  not validate a complete schema or reconcile cent-rounding residuals. It does not
  model whole shares, minimum orders, transaction costs, or FX.
- `drift.py` computes current-minus-target drift. Missing positions are skipped,
  while the supplied total can remain unchanged; invalid totals or incomplete
  positions can therefore produce a plausible but misleading result.
- `rebalance.py` directs contributions toward underweights and estimates a
  post-contribution state. Its sell warning and months-to-target estimate are
  simple heuristics. It does not cover trade constraints, exact residual handling,
  lots, taxes, fees, cash sleeves, or multi-currency execution.
- `prices.py` retrieves Yahoo Finance data and tries exchange suffixes. It adds
  values from different currencies before merely warning about the mismatch,
  broadly catches errors, and does not retain sufficient provider provenance or
  distinguish value timestamp from retrieval time.
- `overlap.py` compares only supplied top holdings. It does not emit look-through
  coverage or holdings dates, so partial exposure can look complete.
- `concentration.py` combines supplied geography and sector splits, but one shared
  coverage counter can hide a missing dimension and coverage is omitted from its
  JSON result.
- `fees.py` provides a transparent TER-weighted scenario. It omits platform,
  transaction, FX, and tax costs, and projected return data could double-count TER
  if the input return series is already net of fund expenses.

The portfolio shape described in the stage instructions includes useful ETF
metadata, target weights, current holdings, exposure breakdowns, and as-of dates.
It is Markdown guidance rather than a versioned executable schema. It lacks clear
Account, Listing, Transaction, Goal, cash, source-provenance, approved-versus-
proposed policy, and coverage models.

No test files were found. The scripts contain limited command-line checks but not
a systematic unit, property, integration, or regression suite.

### Privacy, relevance, and reuse

The workflow places real profile, holdings, context, reports, and archives in the
working project root. That directly conflicts with SteadyFolio's requirement that
all real user state and derived output live under ignored `private/`. The hardcoded
country tax summaries are also time-sensitive, unsourced, and too simplified to
be product facts.

The full research and security-screening flow is unnecessary for a routine monthly
contribution. A staged single-skill shape is useful, but it must route narrowly.

The MIT license permits reuse with its copyright and permission notice. Directly
adopting the current implementation is still not recommended: adapting a few small
ideas or algorithms would require material privacy, schema, validation, and test
work. Host compatibility claims in its README remain unverified until Phase 2
checks official host documentation.

## FinRobot

### Verified capabilities and useful concepts

FinRobot implements AutoGen-based single-assistant, RAG, shadow-review, leader,
and multi-assistant workflows. Role configuration is separated from workflow
construction, and newer equity-report code breaks generation into company,
valuation, risk, competitor, news, and synthesis tasks. Report structures include
source metadata and AI-content disclosure concepts.

Relevant paths:

- `finrobot/agents/workflow.py`
- `finrobot/agents/agent_library.py`
- `finrobot/agents/prompts.py`
- `finrobot/data_source/`
- `finrobot_equity/core/src/modules/equity_agents/agent_manager.py`
- `finrobot_equity/core/src/report/`

The useful SteadyFolio pattern is not the framework itself. It is a bounded
request-specific committee in which specialists consume structured evidence,
calculation tools remain authoritative, sources survive into synthesis, and an
optional critic checks consequential conclusions.

### Quality, privacy, and scope limits

The primary workflow defaults to a disk cache and local code execution in a
`coding` work directory with Docker disabled. The repository also supports file
downloads, generated reports, numerous external data providers, and API-key
configuration. Those defaults are unsafe for a public repository handling private
portfolio context and must not be inherited.

The repository has genuine unit tests in its newer equity modules, but a material
portion of older `test_*.py` files are demonstrations or manual API checks that
print results and catch exceptions. The dependency surface spans AutoGen,
LangChain-style components, report generation, web APIs, databases, and several
market-data services. No upstream tests were run in this audit.

Most of its financial-reporting pipeline, web application, RAG stack, and autonomous
code execution are irrelevant or over-engineered for the intended skill. Apache-2.0
allows compatible reuse subject to its terms, including preservation of applicable
license and notice material. `NOTICE` also identifies trademarks; SteadyFolio must
not adopt FinRobot branding. Conceptual use is preferred over code reuse.

## AI Finance Assistant (Finnie)

### Verified architectural concepts

Finnie builds a LangGraph state machine with an input guard, structured Pydantic
router, parallel domain agents, bounded tool loops, a synthesizer, and an output
guard. The portfolio tool is ordinary deterministic Python rather than arithmetic
inside a prompt. These are useful boundaries for SteadyFolio even if a much smaller
implementation can provide them without LangGraph.

Relevant paths:

- `src/workflow/graph.py`
- `src/state.py`
- `src/agents/orchestrator.py`
- `src/agents/synthesizer.py`
- `src/agents/portfolio/agent.py`
- `src/agents/portfolio/tool.py`
- `src/guardrails/`
- `src/observability/semantic_cache.py`
- `tests/unit/`, `tests/eval/`, and `tests/mcp/`

The exact problem solved is controlled routing: a contribution request should use
the portfolio calculator, while a broader review can selectively add specialists
and synthesis. Fixed loop bounds provide an explicit stop condition.

### Quality, privacy, and licensing limits

The inspected tests include isolated cost-tracker tests, MCP smoke tests, and
LangSmith-backed evaluation suites. Core routing, portfolio mathematics, and
privacy behavior have less local unit coverage than the architecture suggests,
and cloud evaluations require external state. No tests were executed here.

Privacy protections are incomplete for SteadyFolio's standard:

- `src/main.py` includes a query prefix in a trace name when tracing is enabled.
- `src/guardrails/pii.py` stores the original matched PII snippet in its audit list.
- Presidio failures return the original text, so PII redaction fails open.
- OpenAI moderation and the LLM injection classifier also fail open on errors.
- `src/state.py` retains full conversation history, and the semantic cache stores
  full queries and graph results in process memory.

The cache is non-persistent and the graph checkpointer is in-memory, which is safer
than silent disk persistence, but that does not remove disclosure risks to external
LLM, embedding, tracing, moderation, market, and news services.

The repository license permits viewing and learning but expressly withholds general
permission to use or redistribute code. No source may be copied. The architecture
is also over-sized for the MVP: server, UI, MCP transports, semantic embeddings,
observability, and six always-available agent domains are not required.

## Wealthfolio

### Verified capabilities and useful concepts

Wealthfolio has a detailed local-first portfolio domain. It separates account,
asset, listing identity, activity, position, lot, quote, FX, goal, allocation,
valuation, and persistence concerns. Important inspected features include:

- exact `Decimal` quantities and amounts, including string-safe snapshot
  serialization;
- opaque asset identity separated from symbol, exchange MIC, provider symbol,
  instrument type, and quote currency;
- transactions with status, fee, tax, source identifiers, import run,
  idempotency, user-modified protection, and review state;
- tax lots with acquisition-date FX, fee and tax allocation, split handling, and
  source-activity traceability;
- explicit FX contexts for valuation date, acquisition date, and cash-flow date;
- quote timestamps, currencies, provider source, adjusted close, and manual notes;
- allocation taxonomies, drift, contribution cash, minimum trade size,
  whole-share mode, partial-classification warnings, and buy-only, sell, or hybrid
  rebalancing scenarios;
- broad unit, integration, snapshot, property, and end-to-end test organization.

Relevant paths:

- `crates/core/src/accounts/accounts_model.rs`
- `crates/core/src/assets/assets_model.rs`
- `crates/core/src/activities/activities_model.rs`
- `crates/core/src/portfolio/snapshot/positions_model.rs`
- `crates/core/src/portfolio/holdings/holdings_model.rs`
- `crates/core/src/portfolio/allocation_targets/`
- `crates/core/src/fx/`
- `crates/core/src/quotes/`
- `crates/market-data/`
- `docs/features/allocations/rebalance-algorithm.md`
- `docs/architecture/market-data-quotes.md`
- `packages/addon-sdk/src/data-types.ts`

For SteadyFolio, these concepts solve ambiguous ticker identity, mixed-currency
valuation, reproducible cost basis, incomplete classification, provider freshness,
and realistic trade-sizing problems.

### Quality, privacy, and scope limits

This is the strongest inspected calculation design, particularly its use of exact
decimals and dated FX. Its greedy rebalance design documents warnings and
post-filter reconciliation. It is still not automatically correct for SteadyFolio:
tax-aware optimization and multi-account optimization are future work, weights
above 100% may be silently normalized in one allocation path, and the full
accounting engine far exceeds the MVP.

The extensive test inventory is positive evidence of engineering maturity, but
tests were not run and the audit was selective. The application persists accounts,
activities, notes, lots, quotes, goals, provider configuration, backups, and AI
tool outputs. Any analogous SteadyFolio records must remain under `private/`, and
external AI/provider calls must disclose exactly what leaves the local boundary.

The root project is AGPL-3.0, so main-code copying is not recommended before the
project license and distribution model are explicitly resolved. The addon SDK has
its own MIT license, but reuse must be limited to files actually covered by that
subpackage license and must preserve the notice. The desktop/server/frontend,
device sync, brokerage connections, spending, addon runtime, and full accounting
surface are irrelevant for the initial skill.

## Ghostfolio

### Verified capabilities and useful concepts

Ghostfolio models accounts, balances, transaction-like orders, symbol profiles,
market data, currencies, asset classifications, portfolio snapshots, benchmarks,
and portfolio risk rules. Its import fixtures cover successful and invalid data,
including account-free imports, fees, currencies, symbols, dates, and exchange-rate
failures. Portfolio display models distinguish gross/net performance and currency
effects, and core calculations use `big.js` in several portfolio paths.

Relevant paths:

- `prisma/schema.prisma`
- `apps/api/src/app/portfolio/`
- `apps/api/src/services/market-data/`
- `apps/api/src/services/benchmark/`
- `apps/api/src/models/rules/`
- `libs/common/src/lib/models/portfolio-snapshot*.ts`
- `libs/common/src/lib/interfaces/portfolio-*.ts`
- `libs/common/src/lib/calculation-helper.ts`
- `test/import/`

These concepts help SteadyFolio distinguish an instrument from a user transaction,
represent currency effects separately, validate imports with negative fixtures,
and express concentration checks as explainable rules rather than opaque scores.

### Quality, privacy, and scope limits

The repository has a substantial Jest/Nx test inventory and many import fixtures.
No tests were run. Its persistence schema uses database `Float` for quantities,
prices, fees, balances, and market data even though later calculations often use
`Big`; SteadyFolio should use exact decimal input and persistence from the start
instead of crossing that precision boundary.

Ghostfolio is a complete hosted application with PostgreSQL, Prisma, queues,
authentication, API keys, sharing/access grants, subscriptions, analytics, and a
large Angular/NestJS surface. Those features are irrelevant and would create
unnecessary privacy and operations risks. Portfolio data, access tokens, account
metadata, analytics, public-sharing controls, and exports are all sensitive.

The codebase is AGPL-3.0. It should remain a concepts-only reference unless a later
license decision intentionally accepts those obligations. The current project does
not need its server, user-management, public portfolio sharing, paid subscription,
queue, or administrative market-data infrastructure.

## PyPortfolioOpt

### Verified capabilities and assumptions

PyPortfolioOpt provides expected-return estimators, covariance and shrinkage risk
models, efficient frontier variants, semivariance, CVaR, CDaR, critical-line and
hierarchical risk-parity algorithms, Black-Litterman models, objective functions,
constraints, performance metrics, and greedy or linear-programming discrete
allocation.

Relevant paths:

- `pypfopt/expected_returns.py`
- `pypfopt/risk_models.py`
- `pypfopt/efficient_frontier/`
- `pypfopt/objective_functions.py`
- `pypfopt/discrete_allocation.py`
- `pypfopt/hierarchical_portfolio.py`
- `pypfopt/black_litterman.py`
- `tests/`
- `pyproject.toml`

The test suite contains 18 `test_*.py` modules and 317 discovered top-level or
class test functions by static count. It covers input errors, solver variants,
constraints, transaction-cost objectives, discrete allocation, and regression
examples. This is the strongest focused quantitative test inventory among the
Python references, but it was not executed in this audit.

Its models require consequential assumptions about expected returns, covariance,
historical windows, risk-free rates, bounds, objectives, and solver behavior.
Optimization can turn estimation error into precise-looking allocations and is not
needed to answer which underweight approved holding should receive a modest monthly
contribution. The core install brings CVXPY, NumPy, pandas, scikit-learn, SciPy,
and scikit-base; solver and scientific-binary cost is material for a lightweight
skill.

The MIT license permits reuse with its notice. Initial SteadyFolio should not take
the dependency. It can be reconsidered only if Phase 2 deliberately includes an
optimizer-backed feature with documented assumptions, deterministic fixtures,
failure handling, and an understandable non-optimizer baseline.

## Cross-reference component assessment

| SteadyFolio problem | Best reference evidence | What to carry forward | What not to inherit |
| --- | --- | --- | --- |
| Request routing and staged workflow | CoFolio skill; Finnie graph | Narrow intent routing and progressive references | Full agent graph for routine calculations |
| Deterministic contribution allocation | CoFolio `dca.py` and `rebalance.py`; Wealthfolio allocation targets | Pure calculator, buy-only default, exact residual reconciliation | Unvalidated weights, mixed currency, opaque heuristics |
| Instrument and listing identity | Wealthfolio asset and quote models; Ghostfolio symbol profiles | Stable instrument ID plus listing/MIC, provider symbol, quote currency | Ticker-only identity |
| Accounts, transactions, holdings, and lots | Wealthfolio core models; Ghostfolio Prisma schema | Separate source records from derived positions; exact decimals and provenance | Hosted account/auth infrastructure and floating-point persistence |
| FX and valuation | Wealthfolio FX contexts and quote models | Dated rates, currency pair, provider, value time, retrieval time, purpose | Adding unlike currencies and warning afterward |
| ETF look-through and concentration | CoFolio overlap/concentration; Wealthfolio taxonomy exposure; Ghostfolio rules | Coverage, as-of dates, unknown bucket, explainable thresholds | Treating top holdings as complete exposure |
| Research and synthesis | FinRobot report/source structures; Finnie synthesis | Structured evidence, bounded specialists, optional critic | Autonomous code execution, broad RAG, cloud traces by default |
| Advanced optimization | PyPortfolioOpt | Possible later optional adapter | Making estimated efficient-frontier weights the MVP default |

## Public-repository privacy requirements derived from the audit

- Every real profile, goal, account, transaction, holding, target, thesis, cached
  provider result, report, review, prompt transcript, trace, and log belongs under
  ignored `private/` or must not be persisted at all.
- Public fixtures and documentation must remain fully synthetic. Provider responses
  must not be checked in merely because they lack recognizable secrets.
- Logs and audit records must avoid raw prompts, account identifiers, holdings, and
  matched PII snippets. Redaction failure must not silently send raw private data to
  another service.
- External providers require explicit boundaries: fields sent, provider identity,
  source/value date, retrieval time, cache policy, terms, limitations, and failure
  behavior.
- Generated packages must use an allowlist and exclude `private/`, `blueprint/`,
  caches, logs, local configuration, credentials, and database files.
- A proposed target or transaction must remain distinct from an approved persisted
  change. A saved review must not mutate holdings.

## Missing capabilities across the references

No inspected reference provides the required combination unchanged. A new
foundation still needs:

- a versioned, validated, exact-decimal schema for InvestorProfile, Goal, Account,
  Instrument, Listing, Transaction, Holding, HoldingThesis, approved TargetPolicy,
  and proposed changes;
- atomic private-state initialization and writes under `private/`, with no runtime
  memory beside the public skill definition;
- explicit distinction between instrument currency, listing/quote currency,
  account currency, base currency, and underlying economic currency exposure;
- deterministic DCA allocation with cent residual conservation, cash handling,
  whole/fractional constraints, minimum trade values, fees, and insufficient-data
  errors;
- provider-neutral result envelopes carrying provenance, value date, retrieval
  time, freshness, methodology, coverage, and limitations;
- ETF overlap and concentration outputs that preserve unknown exposure and never
  equate missing data with zero;
- offline synthetic unit and property tests for invariants, rounding, missing data,
  invalid weights, mixed currencies, and reproducibility;
- a privacy-safe, request-scoped orchestration layer with bounded retries and calls;
  and
- verified Codex and ChatGPT installation/compatibility behavior from official host
  documentation.

## Initial foundation recommendation for Phase 2 evaluation

The leading candidate is a clean, repository-owned implementation rather than a
fork or embedded upstream application. It should use a small public skill definition
and deterministic Python core, with all real runtime state under `private/`.

Phase 2 should compare that candidate explicitly against adapting CoFolio and using
CoFolio with a separated extension. The initial clean-build case is stronger because
it can preserve CoFolio's useful workflow shape without retaining root-level private
files or weak schemas, avoid AGPL application code, avoid Finnie's non-reuse license,
and defer PyPortfolioOpt and multi-agent frameworks until a verified requirement
justifies them.

This is an audit recommendation, not the final architecture or license decision.
Phase 2 must still verify official host requirements, choose the canonical skill
location, settle the project license and notice plan, define the exact MVP schema and
runtime, and document the tradeoffs among the three permitted foundation options.
