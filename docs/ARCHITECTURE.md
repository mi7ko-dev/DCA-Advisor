# SteadyFolio Architecture

## Status

This document is the proposed Phase 2 architecture. It becomes the implementation
baseline only after the Phase 2 approval checkpoint. It does not authorize Phase 3
implementation, packaging, publishing, or any handling of real portfolio data.

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

## Foundation comparison

| Criterion | A: adapt CoFolio | B: clean skill with selected reference concepts | C: keep CoFolio largely intact and extend it |
| --- | --- | --- | --- |
| Simplicity | Moderate; less initial code, but inherited assumptions need removal | High; only the required paths are built | Low; two conceptual layers and compatibility work |
| Required functionality | Partial; useful staged workflow and calculators | Exact; model and workflow can match SteadyFolio | Broad but still needs a separate domain extension |
| Technical debt | Moderate; weak schemas and root-level state conventions must be corrected | Lowest controllable debt | Highest; legacy boundaries remain while new ones are added |
| Testability | Moderate; existing behavior needs characterization first | High; pure functions and ports can be designed for tests | Moderate to low; behavior spans old and new paths |
| Licensing | MIT permits reuse with notice | Clean-room project code; concepts only by default | MIT permits reuse with notice, but provenance is more complex |
| Privacy fit | Requires material restructuring | Strong; private boundary is a first-class invariant | Weak until the inherited layout is replaced |
| Maintenance | Tied to an upstream shape that is not the desired product model | Smallest stable surface and one calculation engine | Ongoing fork and extension maintenance |
| Host compatibility | Skill shape is useful but not sufficient across hosts | Host-neutral core with explicit adapters and packaging path | Host assumptions remain embedded in the inherited layout |

**Selected foundation: Option B.** The Phase 1 audit found valuable concepts in the
references, but no upstream project combines the required privacy boundary, domain
model, deterministic calculations, license posture, and MVP scope. A clean
implementation avoids importing application-scale frameworks and avoids maintaining
two engines that could disagree.

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

The storage adapter validates JSON against versioned public schemas, constrains all
private paths below the selected workspace, and writes atomically. Initialization
must be non-destructive: existing files are not overwritten without a separate,
explicit operation.

### Provider layer

Provider ports separate source data from interpretation. Offline synthetic fixtures
are the Phase 3 implementation. Future live price, FX, broker, or research adapters
must preserve timestamps, source identifiers, retrieval times, and failure states.

## Proposed repository layout

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
    domain/
    calculations/
    application/
    storage/
    providers/
schemas/
tests/
  fixtures/
examples/
docs/
tools/
private/                 # ignored; real state and derived output
blueprint/               # entirely ignored local reference material
```

Only files needed by the approved phase should be added. An `agents/openai.yaml`
manifest, MCP server, UI, and plugin bundle are deferred until an actual host or
distribution requirement calls for them.

## Runtime and host compatibility

### First supported runtime

The first supported and tested runtime is local Codex operating in this repository,
with Python 3.11 or newer available for the deterministic engine. The repository
policy remains in `AGENTS.md`; the canonical skill is proposed for
`.agents/skills/steadyfolio/`.

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
`private/`, blueprint clones, caches, and repository history cannot enter the
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
| `InvestmentThesis` | Stable ID, instrument/category subject, status, evidence references, assumptions, risks, review date, and supersession link |
| `ContributionPlan` | Stable ID, input amount/currency/date, constraints, proposed buys, fees, residual cash, and algorithm/version; never represented as an executed trade |
| `AnalysisResult` | Stable ID, analysis type/version, input references, as-of time, warnings, metrics, and provenance; immutable derived output |
| `DataSource` | Stable ID, source/provider, source type, value time, retrieval time, units/currency, citation or local reference, and quality/coverage flags |
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
  decimal strings and calculate with `decimal.Decimal`.
- Every monetary amount carries or inherits one explicit ISO 4217 currency.
- Cross-currency valuation requires a dated FX source record. Missing FX causes an
  explicit incomplete result, not an assumed rate or mixed-currency sum.
- `drift = current_weight - approved_target_weight`; positive drift means
  overweight and negative drift means underweight.
- Contribution plans are buy-only by default, do not overspend the available cash,
  account for fees and minimum trade sizes, honor whole/fractional-share settings,
  and report residual cash.
- Calculations do not mutate holdings, transactions, targets, or source data.
- Weights and reconciliations use explicit tolerances and return warnings rather
  than silently normalizing invalid input.
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
              one bounded revision and final synthesis
```

The host orchestrator owns the final answer. A routine monthly contribution does
not trigger research or a critic automatically. By default, one request may use at
most one research pass, one critic pass, and one revision unless the user explicitly
expands the task.

When a host supports true subagents and their use is justified, each role receives
a narrow task and structured inputs. When roles are simulated by sequential calls
to the same model, outputs must be described as review lenses, not independent
verification or consensus. Deterministic tests and source provenance remain the
evidence; model agreement is not evidence.

## Phase 3 MVP boundary

### Included after approval

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

## Verification strategy

Phase 3 changes must pass repository privacy checks and Gitleaks as well as domain
tests. Pure functions receive exhaustive boundary tests. Application tests use a
temporary workspace and synthetic fixtures. Golden reports may assert stable
structure and facts, but calculations are asserted against structured JSON rather
than prose. Provider tests must cover unavailable, stale, contradictory, and
incomplete data without network dependence.

The package boundary must also have a test that inventories an allowlisted build and
fails if ignored paths, private instances, blueprint clones, VCS metadata, or local
caches are present.

## Licensing and provenance

The proposed project license is MIT, subject to explicit approval and addition of a
repository license file in a later authorized change. Phase 3 should be clean-room
project code based on documented requirements and general concepts.

- CoFolio and PyPortfolioOpt are MIT at the audited commits. If code is later copied
  or adapted, their applicable copyright and license notices must accompany it.
- FinRobot is Apache-2.0 with a `NOTICE`; any later reuse must preserve applicable
  license/notice obligations and must not adopt its trademarks.
- Finnie's inspected license does not grant general redistribution or reuse, so it
  is architecture-only reference material.
- Wealthfolio and Ghostfolio main repositories are AGPL-3.0. Their main-project code
  will not be reused under this proposal. Any separately licensed subcomponent needs
  a file-level license review before use.

No copied upstream code is part of this Phase 2 proposal. License observations are
engineering constraints, not legal advice.

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
