# SteadyFolio Architecture

## Status

This Phase 2 architecture was approved as the Phase 3 implementation baseline on
2026-09-25. The approval covers the bounded local MVP described here; it does not
authorize packaging, publishing, later phases, or handling real portfolio data in
tracked files.

## Decision summary

SteadyFolio will use a clean, repository-owned implementation rather than adapting
an upstream application. The first runtime will be a local Codex repository
workspace. A small Python 3.11+ deterministic engine will own validation,
calculations, persistence rules, and report data. The host skill will own workflow,
explanations, and optional review lenses.

The canonical public skill will live at `.agents/skills/steadyfolio/`. Real user
state and every output derived from it will live below an explicitly selected
workspace root in its ignored `private/` directory. Public schemas, tests, examples,
and documentation will contain synthetic data only. JSON and Markdown are the MVP
storage formats; SQLite is deferred until a demonstrated query, scale, or migration
need exists.

The MVP deliberately excludes a web server, live brokerage integration, automatic
trading, broad market research, tax advice, credential storage, and advanced
portfolio optimization.

## System boundary

```text
Codex / future compatible host
            |
            v
  SteadyFolio skill workflow
  - intent and approval gates
  - optional bounded review lenses
  - human-readable synthesis
            |
            v
  Python application services
  - initialize / validate / analyze / plan / report
            |
            v
  Deterministic domain engine
  - typed domain records
  - Decimal calculations
  - constraint and invariant checks
            |
        +---+-------------------+
        |                       |
        v                       v
  private workspace       provider ports
  JSON source/state       FX / price / research
  Markdown reviews        (offline fixtures first)
```

The skill is not the calculation engine. It calls stable application operations and
explains their structured results. Financial arithmetic and validation remain in
ordinary Python so the same inputs produce the same outputs regardless of host.

## Layers and ownership

### Skill layer

The skill routes requests, loads only the references needed for the current task,
enforces approval points, and turns structured engine output into user-facing
explanations. It must not contain a second implementation of allocation, FX, fee,
or drift calculations.

### Application layer

Application services coordinate use cases such as workspace initialization,
validation, portfolio analysis, contribution planning, and report generation. They
depend on domain interfaces rather than host APIs or storage internals.

### Domain and calculation layer

Domain records define the public schema contract. Pure calculation functions use
`decimal.Decimal`, explicit currency contexts, and explicit dates. They do not read
files, call models, fetch network data, or mutate source records.

### Storage layer

The storage adapter validates JSON against the versioned public data contract and
domain invariants, constrains all private paths below the selected workspace, and
writes atomically. Initialization is non-destructive: existing files are not
overwritten without a separate, explicit operation.

### Provider layer

Structured source records separate supplied data from interpretation. Phase 4 adds
a replaceable research-provider protocol and an offline synthetic provider. The
request boundary carries public instrument/listing identifiers, explicitly
referenced public evidence-source identifiers, and an as-of date, not portfolio
quantities or personal context. Future live price, FX, broker, or research adapters
must preserve timestamps, source identifiers, retrieval times, methodology, terms,
limitations, and failure states.

## Repository layout

```text
AGENTS.md
README.md
.gitignore
.agents/
  skills/
    steadyfolio/
      SKILL.md
      references/
      scripts/
src/
  steadyfolio/
    models.py
    validation.py
    calculations.py
    storage.py
    reporting.py
    providers.py
    research_models.py
    research_validation.py
    intelligence.py
    intelligence_reporting.py
    thesis.py
schemas/
tests/
examples/
docs/
tools/
private/                 # ignored; real state and derived output
```

Phase 5 adds the canonical skill under `.agents/skills/steadyfolio/` and its
minimal `agents/openai.yaml` UI metadata. An MCP server, UI, generated plugin
bundle, and additional host adapters remain deferred until an approved phase or an
actual host requirement calls for them.

## Runtime and host compatibility

### First supported runtime

The first supported and tested runtime is local Codex operating in this repository,
with Python 3.11 or newer available for the deterministic engine. The repository
policy remains in `AGENTS.md`; a later approved phase may add the canonical skill
at `.agents/skills/steadyfolio/`.

This follows the official OpenAI description of repository instructions and
repo-local skills:

- [Skills in the OpenAI Agents SDK](https://developers.openai.com/blog/skills-agents-sdk)
- [Skills concepts](https://developers.openai.com/plugins/concepts/skills)
- [Building skills](https://developers.openai.com/plugins/build/skills)

The official material also describes progressive disclosure: hosts discover skill
metadata, load `SKILL.md` when selected, and load supporting references or scripts
only when required. SteadyFolio should use that shape to keep the public skill small
and the runtime context focused.

### Portability path

The Python core is host-independent. A later, explicitly authorized packaging step
may generate a portable plugin bundle from the canonical skill and engine according
to [OpenAI's plugin packaging guidance](https://developers.openai.com/plugins/build/plugins).
Generated packaging must use an allowlist and a temporary output directory so
`private/`, caches, and repository history cannot enter the
bundle. The target ChatGPT/Codex host must then be tested; compatibility is not
assumed from directory shape alone.

No MCP server or network service will be added merely to claim wider compatibility.
A server is justified only when a future host requires a remote tool boundary or a
genuine shared service.

## Workspace and privacy boundary

Skill installation and user data are separate roots:

```text
repository / installed skill            explicitly selected workspace root
--------------------------------        ----------------------------------
public instructions                     private/
public Python package                      state/
public JSON schemas                        source-data/
synthetic examples and tests               reviews/

tracked and distributable                ignored and never packaged
```

The workspace root must be supplied explicitly by the caller or a documented CLI
argument. It must not be inferred from a home directory, recent file, or hidden host
state. The storage layer resolves `private/` from that root, rejects traversal and
symlink escapes, and never writes to the skill installation directory.

Public examples and test fixtures must be obviously synthetic. Logs, debug dumps,
provider responses, reports, and intermediate calculations derived from a real user
belong under `private/`, even if they appear anonymized.

## Domain model

All public schemas are versioned. Private files are instances of those schemas, not
alternative undocumented formats.

| Entity | Purpose and minimum representation |
| --- | --- |
| `InvestorProfile` | Stable ID, base currency, jurisdiction code, risk/constraint declarations, and links to goals; no credentials or account identifiers in public data |
| `Goal` | Stable ID, name, horizon/date, priority, optional target amount and currency, and constraints |
| `Instrument` | Stable internal ID, type, name, identifiers such as ISIN when available, economic currency/exposure metadata, and classification |
| `Listing` | Stable ID, instrument ID, MIC, exchange ticker, trading currency, and provider-symbol mappings; listings do not replace instrument identity |
| `Account` | Stable ID, type, provider label, currency context, and jurisdiction attributes; authentication data is never stored |
| `Holding` | Account ID, instrument/listing ID, quantity, optional acquisition metadata, and source/as-of references |
| `Transaction` | Stable ID, account, instrument/listing, type, trade date, settlement date when known, quantity, price, fees, taxes, and currencies |
| `TargetAllocation` | Stable versioned ID, status (`proposed` or `approved`), effective date, instrument/category targets, rationale, and approval metadata |
| `InvestmentThesis` | Stable ID, instrument subject, status, role, rationale, approved target reference/range, benchmark, risks, review triggers, last review, and next review |
| `ContributionPlan` | Stable ID, input amount/currency/date, constraints, proposed buys, fees, residual cash, and algorithm/version; never represented as an executed trade |
| `AnalysisResult` | Stable ID, analysis type/version, input references, as-of time, warnings, metrics, and provenance; immutable derived output |
| `DataSource` | Stable ID, source/provider, source type, value time, retrieval time, units/currency, citation or local reference, and quality/coverage flags |
| `ResearchSnapshot` | Structured fund facts, partial holdings, classified exposures, compatible historical series, source methodology/freshness/terms, and no raw provider payload |
| `ReviewHistory` | Stable ID, reviewed object/version, reviewer kind, decision, timestamp, findings, and supersession link |

Jurisdiction-specific tax, suitability, account, or disclosure rules live in
separate policy records or adapters. They must not be hard-coded into the global
instrument or calculation schema.

## Required separations

The following distinctions are schema and workflow invariants:

- Approved target allocations are immutable policy versions; proposed targets
  cannot silently replace them.
- Transactions represent recorded events; contribution suggestions are plans and
  never appear as executed activity until the user records an execution separately.
- Public schemas define structure; real instances remain in ignored private storage.
- Skill instructions are public behavior; durable user memory is private data.
- Provider/source records retain the supplied facts; generated analysis and
  interpretation reference those facts without rewriting them.
- An instrument is the economic asset; a listing is a venue-specific tradable form.
- Trading currency is the listing/order currency; economic currency describes the
  underlying exposure and must not be inferred from the ticker or exchange alone.

## Calculation conventions and invariants

- Persist monetary values, quantities, prices, FX rates, weights, and fees as
  canonical decimal strings and calculate with `decimal.Decimal`.
- Every monetary amount carries or inherits one explicit ISO 4217 currency.
- Cross-currency valuation requires a dated FX source record. Missing FX causes an
  explicit incomplete result, not an assumed rate or mixed-currency sum.
- `drift = current_weight - approved_target_weight`; positive drift means
  overweight and negative drift means underweight.
- Contribution plans are buy-only by default, do not overspend the available cash,
  account for fees and minimum trade sizes, honor whole/fractional-share settings,
  and report residual cash.
- Calculations do not mutate holdings, transactions, targets, or source data.
- Weights and reconciliations use explicit tolerances. A target allocation that is
  valid within tolerance is normalized once for every downstream calculation;
  input outside tolerance is rejected.
- Structured calculation results are revalidated before persistence, and approved
  allocation versions cannot be removed or rewritten by an overwrite.
- Outputs include the calculation version, input references, valuation date,
  provenance, and limitations needed to reproduce the result.

## Workflow and bounded review committee

```text
validated private inputs
        |
        v
deterministic analysis / contribution plan
        |
        +--> routine, low-consequence request --> direct synthesis
        |
        +--> consequential or evidence-dependent request
                 |
                 +--> allocation/diversification/ETF lens
                 +--> risk/cost/constraints lens
                 +--> current-source research (only when needed)
                 +--> critic review (only when needed)
                 |
                 v
              optional bounded revision and final synthesis
```

The host orchestrator owns the final answer. A routine monthly contribution does
not trigger research or a critic automatically. A critic runs only for a material
disagreement. The current implementation independently permits at most one research
pass, one critic pass, one revision, and zero live external calls. A broader
workflow requires a later approved implementation rather than an implicit retry or
scope expansion.

When a host supports true subagents and their use is justified, each role receives
a narrow task and structured inputs. When roles are simulated by sequential calls
to the same model, outputs must be described as review lenses, not independent
verification or consensus. Deterministic tests and source provenance remain the
evidence; model agreement is not evidence.

## Phase 3 MVP boundary

### Implemented

- Versioned public schemas for the entities required by the MVP and safe,
  non-overwriting private-workspace initialization.
- Profile, goals, accounts/holdings, instruments/listings, approved targets, and
  basic investment-thesis records.
- Portfolio market value, current weights, signed drift, simple DCA, and
  drift-aware buy-only DCA.
- Whole- and fractional-share constraints, minimum trades, weighted fees, residual
  cash reconciliation, and basic concentration indicators.
- Explicit multi-currency valuation inputs and clear missing-FX failures.
- Structured JSON results plus a concise English Markdown report using synthetic
  examples only.
- Unit, schema, integration, privacy, and invariant tests, including equal-weight,
  drifted, zero-value, multi-currency, missing-FX, fee, and no-overspend cases.

The primary acceptance scenario is a fully synthetic monthly EUR 400 contribution.
It must demonstrate that suggested purchases respect costs and constraints, never
sell, never overspend, preserve input files, and reconcile purchases plus fees plus
residual cash to the available amount.

### Deferred

- Live brokers, order placement, credentials, account synchronization, and personal
  finance aggregation.
- Live market/news research, autonomous browsing, background monitoring, and
  unbounded multi-agent execution.
- Tax computation, regulated suitability determinations, and jurisdiction-specific
  recommendations.
- Efficient-frontier or other estimated optimization, tax-loss harvesting, lot
  optimization, derivatives, leverage, and automated rebalancing sales.
- Web/mobile/desktop UI, database server, authentication, cloud sync, telemetry,
  hosted API, and MCP server.
- SQLite or another database until JSON limitations are demonstrated and a migration
  plan is approved.

## Phase 4 intelligence boundary

Phase 4 implements structured fund metadata, partial holdings overlap, observed
company/issuer concentration, classified sector/geography/currency exposure,
compatible-series historical metrics, benchmark comparison, stress windows, source
freshness and terms metadata, and non-mutating thesis review. Detailed formulas and
limitations are in `docs/RESEARCH.md`.

Only the offline synthetic provider is implemented. Live providers, autonomous web
research, raw-response caching, tax/regulatory conclusions, forecasting, and policy
mutation remain deferred. A future adapter must review provider terms before using
or persisting data and must store real user-related responses and outputs below
`private/`.

## Phase 5 conversational workflow boundary

Phase 5 implements the canonical repo-local skill, deterministic request routing,
structured committee results, selective sequential review lenses, an optional
single critic pass, and non-mutating private review persistence. The output keeps
facts, source dates, limitations, assumptions, interpretations, disagreements, and
proposals distinct and records the tools and lenses actually used.

Routine contribution planning remains a direct deterministic path. Portfolio,
overlap, and thesis reviews invoke only their relevant lenses. Missing or stale
evidence, an empty snapshot, or zero overlap coverage can stop the workflow with
`insufficient_evidence`; agreement between lenses is never treated as correctness.
Details are in `docs/COMMITTEE.md`.

The selected host is local Codex in this repository. The skill is discovered in the
current repository session, and its structure and metadata pass the bundled skill
validator. No clean-machine or global installation, generated plugin, ChatGPT host,
MCP service, live provider, or true multi-agent runtime is implemented or claimed.

## Verification strategy

Phase 3 changes must pass repository privacy checks and Gitleaks as well as domain
tests. Pure functions receive exhaustive boundary tests. Application tests use a
temporary workspace and synthetic fixtures. Golden reports may assert stable
structure and facts, but calculations are asserted against structured JSON rather
than prose. Provider tests must cover unavailable, stale, contradictory, and
incomplete data without network dependence.

No separate artifact is required for the supported repository-local Codex use. If a
future host requires packaging, its implementation must inventory an allowlisted
build and fail if ignored paths, private instances, VCS metadata,
or local caches are present. It must also inspect the artifact and clean-install it
before a separately approved publication.

## Licensing and provenance

The approved project license is MIT and the repository includes the corresponding
license file. Phase 3 is clean-room project code based on documented requirements
and general concepts. No copied upstream code is part of the implementation. Any
future copied or adapted code requires a file-level provenance, license, notice,
and trademark review before it enters the repository. These are engineering
constraints, not legal advice.

The completed implementation has no runtime third-party dependency and redistributes
no upstream code, so it does not require a third-party notice file. The project MIT
license remains the only current distribution notice.

## Known limitations

- Host portability is a planned adapter and packaging path, not a verified promise.
- JSON is appropriate for the small local MVP but does not provide concurrent
  writers, complex queries, or large-scale migrations.
- The MVP cannot infer economic exposure, FX, prices, or jurisdiction rules from a
  ticker alone; incomplete source data produces incomplete analysis.
- Contribution allocation is an explainable heuristic, not a forecast or guarantee
  of performance.
- Review lenses reduce blind spots but do not create independent financial advice,
  factual verification, or regulatory approval.
