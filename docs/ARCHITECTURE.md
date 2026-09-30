# SteadyFolio Architecture

## Status

This Phase 2 architecture was approved as the Phase 3 implementation baseline on
2026-09-25. The approval covers the bounded local MVP described here; it does not
authorize packaging, publishing, later phases, or handling real portfolio data in
tracked files.

## Decision summary

SteadyFolio uses a clean, repository-owned implementation rather than adapting an
upstream application. The first runtime is a local Codex repository workspace. A
small Python 3.11+ deterministic engine owns validation, calculations, persistence
rules, and report data. The host skill owns workflow, explanations, sequential
review lenses for legacy routes, and bounded Codex-native subagent orchestration
for Phase 8 equity review.

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
  - bounded equity specialist/critic subagents
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
    agent_models.py
    generic_agent_models.py
    generic_agents.py
    validation.py
    calculations.py
    storage.py
    private_records.py
    reporting.py
    providers.py
    research_models.py
    research_validation.py
    intelligence.py
    intelligence_reporting.py
    multi_agent.py
    thesis.py
schemas/
tests/
examples/
docs/
tools/
private/                 # ignored; real state and derived output
```

Phase 5 adds the canonical skill under `.agents/skills/steadyfolio/` and its
minimal `agents/openai.yaml` UI metadata. Phase 8 adds host-native Codex subagent
instructions and Python contracts, not an MCP server or model API client.

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
- [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)

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
symlink escapes, and never writes to the skill installation directory. When that
root is inside a Git worktree, the storage layer fails before creating or accessing
a target unless the exact path is ignored and untracked.

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
        +--> non-equity consequential request
                 |
                 +--> private cache inspection
                 +--> one lead-owned current-source research pass (when needed)
                 +--> two or three isolated specialist threads (when triggered)
                 +--> one isolated critic thread
                 |
                 v
              one lead synthesis; no vote or retry

        +--> equity_review
                 |
                 +--> review_equity exactly once
                 +--> immutable role-minimal packets
                 +--> four isolated Codex specialist threads
                 +--> one isolated critic thread
                 |
                 v
              one lead synthesis; no vote or retry
```

The host orchestrator owns the final answer. A routine monthly contribution does
not trigger research or a critic automatically; missing or stale price, FX,
approved-target, or constraint input produces the route stop condition unless a
material conflict beyond the calculation is explicitly escalated. Phase 9 consequential non-equity reviews use the
smallest useful set of two or three isolated roles plus one critic. Equity review
retains its strict four-role packet contract. The lead may perform at most one
host-native web research pass after inspecting the private cache; specialists do
not browse. Every agent runs once, with one critic and one synthesis, and there is
no retry or debate loop.

Phase 8 selects Codex host-native subagents for `equity_review`. The main Codex
thread is `LeadOrchestrator`; four specialist threads and one critic thread receive
immutable schema `1.1` packets and return strict schema `1.1` results. Packet IDs
bind a canonical digest of the complete packet content, and caller-provided source
IDs are replaced with packet-local opaque aliases. Local Python
prepares and validates contracts but never impersonates an agent. A host without
subagent controls returns `runtime_type=none` and
`fallback_status=deterministic_only`. Deterministic tests and source provenance
remain the evidence; model agreement is not evidence.

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
- A Python live market-data provider, real-time feeds, background monitoring, and
  unbounded multi-agent execution. Phase 9 permits bounded foreground host-native
  web research only.
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

Only the offline synthetic Python provider is implemented. Phase 9 allows the
Codex lead to perform one bounded foreground web research pass and save permitted
derived evidence under `private/research/`; this does not turn the provider port
into a live adapter. Raw-response caching, background monitoring,
tax/regulatory conclusions, forecasting, and policy mutation remain deferred. A
future adapter must review provider terms before using or persisting data and must
store real user-related responses and outputs below `private/`.

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

## Phase 7 equity-review boundary

Phase 7 adds a strict public `EquityReviewInput` contract, deterministic instrument
identity matching, transparent individual-equity quality criteria, separate
valuation and owner-earnings results, and an explicit portfolio-policy evaluator.
The skill routes an individual-stock request to `review_equity` only when structured
dated evidence is supplied. Sequential equity-quality and valuation-evidence lenses
interpret the result without recalculating it.

Personal holdings, thresholds, exemptions, factor groups, and outputs remain under
`private/`. The public repository contains only schemas and synthetic examples.
There is still no live market provider, broker connection, net-liquidation cash
model, tax or regulatory adapter, forecast, transaction execution, or policy
mutation. Exact methodology is in `docs/EQUITY_REVIEW.md`.

The selected host remains local Codex. The canonical repo-local skill is also
packaged in a self-contained Codex plugin with the deterministic Python core,
schemas, synthetic examples, and operating documentation. The plugin is generated
from an explicit public-file allowlist and exposed through the repo-local
`steadyfolio-local` marketplace. Its manifest, skill structure, exact inventory,
and isolated runtime import are tested. No general ChatGPT host, MCP service, or
live provider is implemented. Phase 8 true multi-agent execution is provided only
by Codex host-native subagent threads; it is not provided by the Python engine, an
Agents API client, or the in-memory test backend. Plugin installation does not
install the bundled Python package; the skill uses an explicit, validated `src`
path for direct imports, and CI tests that documented bootstrap independently of
repository source paths or ambient `PYTHONPATH`.

## Phase 8 multi-agent equity-review boundary

Phase 8 applies only to `equity_review`. `prepare_multi_agent_equity_review` calls
the deterministic engine exactly once and creates separate packets for evidence,
business quality, valuation, and portfolio risk. The host starts one isolated
thread per packet, validates every result, starts one critic with only validated
outputs, and performs one final synthesis. Invalid citations, malformed output,
timeouts, unavailable agents, unsupported claims, and contradictions limit or
close the result; there is no retry or debate loop.

The public execution trace stores role, status, execution ID, runtime, bounds, and
generic limitations, not prompts or raw responses. Real packets and derived
results remain in memory or under ignored `private/`. Role-minimal facts are sent
to the Codex model service, which adds hosted processing, token consumption, and
latency. The implementation adds no API key, Agents SDK, Agents API client, MCP
server, or third-party Python dependency. Runtime, attempt, isolation, and raw host
execution identity are owned by the lead; model output cannot set them, and the
trace stores only opaque digests for execution/result correlation.

## Phase 9 current-source, context, and broader review boundary

Phase 9 changes the Codex skill workflow, not the deterministic calculation
engine or offline `ResearchProvider`. For time-sensitive conclusions, the lead
first evaluates compatible immutable records through the public typed list API,
then uses
one bounded host-native web research pass when the cache is not fit for purpose.
Primary sources are preferred, delayed data is labelled, conflicting evidence is
preserved, and source terms govern what may be cached. The lead records source and
retrieval dates, methodology, coverage, limitations, freshness basis, and cache
permission. Queries contain only public identifiers and dates; one pass is bounded
to four targeted searches and eight source documents. Unknown retention terms
default to citation metadata only or no persistence. Evidence may still be used
only in memory when its terms permit current access, analysis, and citation but
prohibit retention. The lead never converts
missing data into a model estimate.

Research and context records are created and saved only through typed public APIs
that validate schemas, choose record-ID-derived collision-resistant names, reject
duplicate identities even when copied timestamps differ, reuse ignored-target and
symlink checks, and expose no overwrite option. The skill creates minimal append-only records below `private/context/` for
durable confirmed facts, user decisions, temporary assumptions, proposals, and
external evidence. Categories remain semantically distinct: a proposal or
temporary assumption cannot become approved policy through reuse. Corrections add
a superseding record instead of rewriting history. This standing persistence
authority does not cover saved reviews or any portfolio-state mutation.

For consequential, uncertain, conflicting, or bias-sensitive supported reviews,
the host starts the smallest useful set of at least two isolated specialists and
one later critic. The lead alone browses and runs deterministic tools; specialists
receive role-minimal prepared evidence and may not use tools, read files,
recalculate, or add facts. Equity review keeps the Phase 8 schema and four roles.
Generic packets and outputs use separate version `1.0` schemas, route-specific
role and aggregate allowlists, content-bound packet IDs, opaque user-owned
identifiers, review-bound source dates, private-context/prompt/path guards, and
packet-only contexts with no inherited history. Exact-field
parsers attach host-owned execution metadata and validate every evidence reference
before critic or synthesis use. The generic critic builder accepts only validated
specialist results. Packet, result, or isolation failure triggers fallback, and all
agent artifacts stay memory-only without immediate persistence approval. Fewer
than two valid generic specialists cannot be reported as multi-agent. If subagents are unavailable, equity reports
`deterministic_only`; non-equity routes report `single_thread_sequential`. Neither
fallback is called multi-agent.

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
- Codex subagent isolation is a host capability, not an operating-system proof that
  a model thread cannot access tools inherited from its parent. Role instructions
  forbid tool use and file reads; the lead sends only the immutable packet.
