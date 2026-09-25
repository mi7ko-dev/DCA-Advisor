# Architecture Decision Record

## Status and use

The decisions below were approved as the Phase 3 baseline on 2026-09-25. That
approval authorizes the bounded implementation scope, but not committing, pushing,
packaging, publishing, later phases, or tracked real user data.

## D-001: Use a clean repository-owned foundation

- **Status:** Accepted
- **Decision:** Select Option B: a clean SteadyFolio skill and deterministic engine
  that adopt reviewed concepts, not an upstream application's structure.
- **Why:** This is the smallest option that satisfies the public/private boundary,
  explicit schema, deterministic testing, and narrow MVP without a compatibility
  layer or application-scale dependencies.
- **Rejected:** Adapting CoFolio directly would require replacing important state
  and schema assumptions. Keeping it intact plus an extension would produce two
  overlapping product models and the highest maintenance cost.
- **Consequence:** Phase 3 must implement only approved behavior and cannot copy
  source merely because a reference repository is public.

## D-002: Support local Codex first

- **Status:** Accepted
- **Decision:** The first supported runtime is local Codex in the repository, with
  Python 3.11+ for deterministic operations.
- **Why:** It gives the MVP an explicit, testable execution environment while
  keeping the core independent of the conversational host.
- **Consequence:** General ChatGPT or plugin compatibility is not claimed until a
  generated package is tested in that target host.

## D-003: Keep one canonical public skill

- **Status:** Accepted
- **Decision:** Store the canonical skill at
  `.agents/skills/steadyfolio/SKILL.md`, with narrowly loaded public references and
  scripts below that directory.
- **Why:** Official OpenAI guidance documents `.agents/skills/` for repo-local
  skills and progressive loading of `SKILL.md` and supporting resources.
- **Consequence:** Do not maintain a second tracked copy for another host. A future
  plugin must be generated from the canonical sources under an explicit packaging
  operation.

## D-004: Use one small Python calculation engine

- **Status:** Accepted
- **Decision:** Implement domain records, validation, calculations, storage rules,
  and structured results in a host-independent Python package. Use the standard
  library and `decimal.Decimal` unless a dependency has a demonstrated need.
- **Why:** Pure Python functions are deterministic, portable, inspectable, and easy
  to test. They prevent prompt logic from becoming an unversioned second engine.
- **Consequence:** NumPy, pandas, CVXPY, PyPortfolioOpt, LangGraph, AutoGen, and a
  server framework are outside the MVP.

## D-005: Use JSON and Markdown private storage in the MVP

- **Status:** Accepted
- **Decision:** Use versioned JSON for private state/source records and structured
  results, and Markdown for human-readable reviews. Resolve all real data below the
  selected workspace root's ignored `private/` directory.
- **Why:** The MVP is local and small, so transparent, diffable formats are easier
  to inspect and migrate than an early database.
- **Consequence:** SQLite is deferred until concurrent access, query complexity,
  scale, integrity, or migration evidence justifies it. Storage writes must validate
  first, be atomic, and avoid overwriting existing state during initialization.

## D-006: Make arithmetic and currency semantics explicit

- **Status:** Accepted
- **Decision:** Persist numeric financial fields as decimal strings and calculate
  with `Decimal`. Identify trading and economic currencies separately. Require dated
  FX provenance for cross-currency totals. Define drift as current weight minus
  approved target weight.
- **Why:** Binary floating-point, ticker-only identity, and implicit FX are unsafe
  foundations for explainable allocation output.
- **Consequence:** Positive drift always means overweight. Missing FX creates an
  incomplete result rather than a guessed conversion or mixed-currency total.

## D-007: Separate policy, reality, and proposals

- **Status:** Accepted
- **Decision:** Keep approved target versions separate from proposed targets;
  recorded transactions separate from contribution plans; public schemas separate
  from private instances; instructions separate from memory; and source records
  separate from generated interpretation.
- **Why:** These boundaries prevent a recommendation from masquerading as user
  approval, an execution, or a sourced fact.
- **Consequence:** Changes of status require explicit operations and history.
  Analysis outputs reference immutable input versions and never mutate them.

## D-008: Use a bounded, conditional review committee

- **Status:** Accepted
- **Decision:** The orchestrator may request an allocation/diversification lens, a
  risk/cost/constraints lens, current-source research, and a critic review only when
  consequence or evidence needs justify them. Default maximum: one research pass,
  one critic pass, and one revision.
- **Why:** Routine DCA calculations need determinism, not an expensive agent graph.
  Consequential recommendations benefit from distinct questions and explicit
  criticism.
- **Consequence:** Same-model sequential calls are labeled review lenses, not
  independent agents or verification. Native subagents are optional host behavior,
  not a dependency of the calculation engine.

## D-009: Preserve provider provenance through ports

- **Status:** Accepted
- **Decision:** Model price, FX, and research retrieval behind provider interfaces.
  Every source record carries provider/source identity, value time, retrieval time,
  units/currency, and quality or coverage status.
- **Why:** Reproducibility and stale/missing-data handling matter more than a broad
  initial integration list.
- **Consequence:** Phase 3 uses offline synthetic fixtures. Live providers, broker
  connections, and autonomous research are deferred.

## D-010: Freeze a narrow Phase 3 MVP

- **Status:** Accepted
- **Decision:** Phase 3 covers schemas, safe private initialization, core portfolio
  records, valuation/current weights/signed drift, simple and drift-aware buy-only
  DCA, fees and trading constraints, basic concentration, structured output, an
  English synthetic report, and tests.
- **Why:** This is the smallest end-to-end slice that proves the model, privacy
  boundary, and calculation invariants.
- **Consequence:** The acceptance scenario is a synthetic EUR 400 monthly
  contribution supporting whole or fractional shares, fees, minimum trades, and
  residual cash, with no selling, overspending, source mutation, or missing-FX
  guesses. Live integrations, UI, tax logic, optimization, databases, and servers
  remain deferred.

## D-011: Propose MIT and require clean-room provenance

- **Status:** Accepted
- **Decision:** Use MIT for SteadyFolio with the repository license file added in
  Phase 3. Prefer concepts and independently authored code. Record required notices
  before any file-level upstream reuse.
- **Why:** MIT fits a small portable public skill, but the audited references have
  different obligations: MIT, Apache-2.0 plus notice/trademark terms, AGPL-3.0, and
  source-viewing-only terms.
- **Consequence:** Finnie code and AGPL application code from Wealthfolio or
  Ghostfolio are excluded. CoFolio, PyPortfolioOpt, FinRobot, or a separately
  licensed component may be reused only after a specific provenance and notice
  review. This is an engineering policy, not legal advice.

## D-012: Package by allowlist only

- **Status:** Accepted
- **Decision:** Any future distributable plugin is generated into a temporary
  directory from an explicit list of canonical public files.
- **Why:** Copying the repository and then applying exclusions risks publishing
  ignored state, reference clones, caches, or Git history.
- **Consequence:** Packaging needs its own approval, inventory test, host test, and
  license-notice check. `private/`, `blueprint/` clones, `.git/`, caches, and local
  outputs are never package inputs.

## Phase 3 approval effects

Phase 2 approval accepted D-001 through D-012 as the Phase 3 baseline. Any material
change to privacy boundaries, runtime, licensing, schema semantics, or MVP scope
must be recorded here and returned to an approval checkpoint before implementation.

## D-013: Use structured, replaceable research providers

- **Status:** Accepted
- **Decision:** Provider requests carry only public instrument/listing identifiers
  and an as-of date. Providers return validated structured snapshots with source,
  methodology, freshness, limitations, terms, and cache/redistribution metadata.
- **Why:** This keeps the deterministic engine independent of a vendor and avoids
  sending portfolio quantities, balances, accounts, goals, or theses to a data
  provider.
- **Consequence:** Phase 4 implements an offline synthetic provider only. Live
  adapters and their explicit integration tests require a separate provider and
  terms review.

## D-014: Preserve partial coverage instead of extrapolating

- **Status:** Accepted
- **Decision:** Holdings overlap, company concentration, and classified exposures
  use only supplied records and report covered plus unclassified portfolio weight.
- **Why:** Top holdings are not complete fund holdings, and missing exposure is not
  evidence of zero exposure.
- **Consequence:** Observed look-through metrics are lower-bound descriptions. They
  cannot be presented as complete exposure without complete provider coverage.

## D-015: Require compatible historical series

- **Status:** Accepted
- **Decision:** Joint historical analysis requires aligned dates, one base
  currency, frequency, return convention, distribution treatment, and
  corporate-action treatment. Benchmark comparisons use the same contract.
- **Why:** Mixing incompatible inputs produces precise-looking but invalid risk and
  performance metrics.
- **Consequence:** Missing or incompatible series fail or remain explicitly
  unavailable. Historical metrics are descriptive and never forecasts.

## Phase 4 approval effects

Approval to execute Phase 4 accepted D-013 through D-015 for the bounded offline
implementation. It did not authorize a live provider, external data transfer,
tracked real research data, policy mutation, Phase 5 work, or publication.

## D-016: Keep conversational routing deterministic and narrow

- **Status:** Accepted
- **Decision:** Route monthly contribution, portfolio review, fund-overlap, and ETF
  thesis requests through explicit local request types and deterministic engine
  operations. Ambiguous requests stop for clarification.
- **Why:** A narrow router is testable and prevents conversational phrasing from
  becoming a second calculation engine or an implicit authorization channel.
- **Consequence:** Natural-language amount parsing accepts only an explicit
  currency-first decimal form. Broader language support must preserve the same
  structured validation boundary.

## D-017: Implement committee roles as disclosed sequential review lenses

- **Status:** Accepted
- **Decision:** Phase 5 uses only the relevant allocation/diversification,
  risk/cost/evidence, thesis-fit, and evidence-quality lenses over structured engine
  results. It permits at most one research pass, one critic pass, one revision, and
  zero live external calls.
- **Why:** This provides useful challenge and synthesis without a framework
  dependency, unbounded debate, or a false claim of independent verification.
- **Consequence:** Outputs disclose actual tools and lenses. Lens agreement is not
  correctness, conflicting conclusions remain visible, and insufficient evidence
  stops the workflow.

## D-018: Keep proposals and saved reviews non-mutating

- **Status:** Accepted
- **Decision:** Committee execution never changes holdings, transactions, theses,
  or targets. Saving an explicitly authorized committee result writes only below
  `private/reviews/`.
- **Why:** Analysis approval is not transaction or policy approval, and a review
  record must not masquerade as execution.
- **Consequence:** Real transactions and target or policy changes require separate
  explicit approval and future dedicated operations.

## Phase 5 approval effects

Approval to execute Phase 5 accepted D-016 through D-018 for the bounded local
Codex workflow. It did not authorize a live provider, external data transfer, trade
execution, policy mutation, global skill installation, plugin packaging, Phase 6
work, publication, or pushing Phase 5 changes.
