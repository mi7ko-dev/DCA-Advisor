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
- **Rejected:** Adapting an upstream application would require replacing important
  state and schema assumptions. Keeping it intact plus an extension would produce two
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
- **Consequence:** Numerical, optimization, agent, and server frameworks are outside
  the MVP unless a demonstrated requirement justifies them.

## D-005: Use JSON and Markdown private storage in the MVP

- **Status:** Accepted
- **Decision:** Use versioned JSON for private state/source records and structured
  results, and Markdown for human-readable reviews. Resolve all real data below the
  selected workspace root's ignored `private/` directory.
- **Why:** The MVP is local and small, so transparent, diffable formats are easier
  to inspect and migrate than an early database.
- **Consequence:** SQLite is deferred until concurrent access, query complexity,
  scale, integrity, or migration evidence justifies it. Storage writes must validate
  first, be atomic, and avoid overwriting existing state during initialization. A
  target inside a Git worktree must be ignored and untracked before storage creates
  or accesses it; a workspace outside Git remains an explicit safe alternative.

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
- **Why:** MIT fits a small portable public skill, while copied or adapted third-party
  code can introduce different license, notice, copyleft, and trademark obligations.
- **Consequence:** Third-party code may be reused only after a specific file-level
  provenance, license, and notice review. This is an engineering policy, not legal
  advice.

## D-012: Package by allowlist only

- **Status:** Accepted
- **Decision:** Any future distributable plugin is generated into a temporary
  directory from an explicit list of canonical public files.
- **Why:** Copying the repository and then applying exclusions risks publishing
  ignored state, reference clones, caches, or Git history.
- **Consequence:** Packaging needs its own approval, inventory test, host test, and
  license-notice check. `private/`, `.git/`, caches, and local
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

## D-019: Distribute the supported product as repository source

- **Status:** Accepted
- **Decision:** Support the Python source package and the repo-local Codex skill in
  this repository. Do not create a plugin archive merely to complete Phase 6.
- **Why:** Current Codex documentation and the verified host session support
  repository-local discovery from `.agents/skills/`. A second bundle would add a
  drift and privacy-review surface without enabling the selected host.
- **Consequence:** A clean-machine host test and any future plugin or cross-host
  package remain separate work. If required, the artifact must be built from an
  explicit allowlist, inspected, clean-installed, and separately authorized before
  publication.

## D-020: Fail closed at storage, provider, and CI boundaries

- **Status:** Accepted
- **Decision:** Reject symlinks at every private output path component, redact raw
  provider failure details while recording the bounded call, and make CI install
  the source package, regenerate synthetic artifacts, run tests, and scan public
  candidates plus available history with a checksum-pinned Gitleaks binary.
- **Why:** These are the boundaries where an apparently valid local workflow could
  otherwise escape the private root, conceal a failed data dependency, drift from
  committed examples, or publish sensitive content.
- **Consequence:** Expected provider failures return `insufficient_evidence` after
  one call. CI uses only synthetic repository content and uploads no diagnostic or
  scan artifact.

## D-021: Make deterministic ambiguity fail closed

- **Status:** Accepted
- **Decision:** Reject conflicting same-date market inputs, non-canonical decimal
  strings, timezone-free retrieval timestamps, incompatible trading overrides,
  non-comparable holdings dates, undersized historical series, invalid evidence
  kinds, inactive thesis reviews, partial numeric-token matches, and rewrites of
  approved allocation versions. Normalize only target weights already valid within
  tolerance. Fingerprint every plan-defining input, including selected listing
  constraints, in contribution IDs. Treat empty or zero-coverage research as
  missing evidence, and apply critic and revision limits independently. Version
  the stricter historical-series minimum as research schema `1.1` while retaining
  explicit read compatibility for schema `1.0`.
- **Why:** Input order, implicit coercion, missing coverage, and loosely coupled
  orchestration limits can otherwise produce reproducible-looking but unsupported
  financial output.
- **Consequence:** Ambiguous data stops explicitly, zero-target assets need no
  market input, round-lot constraints remain authoritative, derived results are
  validated before persistence, and reports use neutral labels with escaped
  user-controlled table cells.

## Phase 6 approval effects

Approval to execute Phase 6 and address its consolidated review feedback accepted
D-019 through D-021 for final hardening and documentation. It did not authorize
staging, committing, pushing, publishing, plugin generation, live providers,
broker connections, transactions, or policy mutation.

## D-022: Add evidence-limited equity review and explicit private policy

- **Status:** Accepted
- **Decision:** Add a versioned offline individual-equity review with a strict
  ISIN/name/listing identity gate, a positive-free-cash-flow hard screen,
  transparent criteria with unavailable-data handling, a separate valuation
  result, and optional owner-earnings evidence. Add a separate configurable
  portfolio-policy evaluator whose real instances remain private.
- **Why:** These concepts improve evidence discipline without copying a personal
  monolithic stock-analysis prompt, hard-coding current market or jurisdiction
  claims, or turning model output into execution authority.
- **Consequence:** The engine accepts only supplied dated evidence and supported
  valuation methods. It performs no live retrieval, broker access, tax conclusion,
  target mutation, or transaction. Policy checks currently use invested positions
  and explicitly disclose that unmodelled cash is absent from the denominator.

## Phase 7 approval effects

The user's instruction to implement the reviewed stock-analysis concepts accepted
D-022 for this bounded public implementation. It did not authorize staging,
committing, pushing, live providers, broker connections, tax adapters, target
changes, transactions, or publication.

## D-023: Ship a reproducible local Codex plugin marketplace

- **Status:** Accepted
- **Decision:** Package the canonical skill and deterministic runtime as the
  `steadyfolio` plugin in the repo-local `steadyfolio-local` marketplace. Generate
  the bundle from a literal tracked-file allowlist into a temporary directory,
  validate its manifest and skill, test its isolated runtime, and keep an exact
  tracked marketplace manifest under `.agents/plugins/marketplace.json` with the
  corresponding plugin under `plugins/steadyfolio/`.
- **Why:** A real installable plugin removes repository-local discovery as a usage
  requirement while preserving the existing offline engine and privacy boundary.
  A generated allowlist prevents ignored user state, credentials, caches, Git
  history, or unrelated development files from entering the package.
- **Consequence:** The plugin is self-contained for local Codex and requires Python
  3.11 or newer. Canonical sources remain outside the generated mirror; CI rebuilds
  and compares it. The Codex install command copies plugin files but does not install
  the bundled Python package, so direct imports explicitly prepend the plugin's
  `src` directory and never trust ambient `PYTHONPATH`. Plugin installation does not
  authorize live data, broker access, transactions, policy mutation, publication,
  or compatibility claims for other hosts.

## Plugin packaging approval effects

The user's instruction to create an installable plugin accepted D-023 and local
package generation. It did not authorize installation into a personal Codex
profile, staging, committing, pushing, marketplace publication, or a release.

## D-024: Use Codex-native subagents for bounded equity review

- **Status:** Accepted
- **Decision:** Phase 8 uses the Codex host's native subagent threads only for
  `equity_review`. The main thread is the lead orchestrator. It calls deterministic
  `review_equity` once, sends immutable role-minimal packets to evidence, business
  quality, valuation, and portfolio-risk specialists, sends only validated results
  to one critic, and performs one final synthesis. Python functions prepare,
  validate, trace, and test contracts; they are never labeled agents.
- **Why:** Current Codex releases can start separate subagent contexts from skill
  instructions without adding an API key or application dependency. This meets the
  isolation requirement while keeping the deterministic engine portable and the
  plugin dependency-free.
- **Consequence:** A real run is available only on a Codex host with subagents and
  sends each minimal packet to the Codex model service, consuming additional
  tokens and latency. No role retries. Contribution starts no agents. A missing or
  failed runtime produces an explicit deterministic or partial fallback and is not
  described as multi-agent. The Agents SDK and Agents API remain unimplemented.
  Agent output contains analysis fields only; the lead attaches host-observed
  runtime, attempt, isolation, and opaque execution/result identifiers.

## D-025: Version agent contracts without redefining deterministic equity v1

- **Status:** Accepted
- **Decision:** Add agent-input, specialist-result, and multi-agent-review schema
  version `1.0`, and CommitteeResult version `2.0` for the agent envelope. Preserve
  deterministic `EquityReviewResult` version `1.0` and CommitteeResult version
  `1.1` compatibility instead of silently changing their meanings.
- **Why:** Agent interpretation is secondary metadata around the deterministic
  result, not a new calculation model. Separate versions make migration and
  fallback behavior explicit.
- **Consequence:** Committee schema `1.1` rejects an agent envelope; version `2.0`
  requires one. The in-memory backend is allowed only for synthetic tests and is
  disclosed as not being a live subagent runtime.

## Phase 8 approval effects

The user's explicit architecture approval accepted the hosted Codex subagent data
flow, additional model-token use, and Phase 8 implementation. It did not authorize
staging, committing, pushing, plugin installation, publication, private-output
persistence, transactions, holdings changes, thesis changes, or policy mutation.

## D-026: Produce deterministic local release archives

- **Status:** Accepted
- **Decision:** Release `0.2.1` adds an outside-repository ZIP containing the exact
  allowlisted marketplace root. The archive uses sorted paths, fixed timestamps,
  fixed regular-file modes, deterministic compression settings, and the canonical
  semantic version without a Codex cache-buster suffix.
- **Why:** A ready marketplace archive makes offline installation reproducible
  without weakening the public/private package boundary or treating installation
  as publication.
- **Consequence:** `tools/build_release.py` rejects repository-local output and
  noncanonical filenames. Every archive must be built twice, compared byte for
  byte, inspected, extracted, validated, runtime-smoke-tested, and reported with a
  SHA-256 checksum. The archive remains outside Git unless separately approved.

## Release 0.2.1 approval effects

The user's release instruction authorizes the semantic-version update, local
allowlisted build, local Codex reinstall, and outside-repository installation
archive. It does not authorize staging, committing, pushing, or publishing the
archive or marketplace.

## D-027: Use bounded host-native research with immutable private caching

- **Status:** Accepted
- **Decision:** When a conclusion materially depends on time-sensitive external
  facts, the Codex lead inspects compatible records under `private/research/` and
  automatically performs at most one host-native web research pass when the cache
  is missing, stale, contradictory, or inadequate. It prefers primary sources,
  records as-of and retrieval dates, methodology, limitations, freshness basis,
  and cache terms, and creates a new immutable private record rather than
  overwriting an earlier one. Specialists receive the prepared evidence and do
  not browse independently.
- **Why:** Valuation and evidence-sensitive review should not rely on remembered
  or silently stale facts, while repeated retrieval should be avoided when a
  compatible and sufficiently current private record already exists.
- **Consequence:** The skill may use the host's available web capability without
  asking for advance permission. This is foreground research, not a Python live
  provider, real-time price feed, background monitor, or authorization to cache
  content against source terms. Queries contain only public instrument/source
  identifiers and dates, one pass is capped at four searches and eight documents,
  and unknown cache terms default to citation metadata only or no persistence.
  Research records are created, saved, and listed only through typed public APIs
  with schema, ignored-target, symlink, and exclusive-create validation. Evidence
  that permits current use and citation but prohibits retention may remain in
  memory for the current review; missing, unusable, unverifiable, or conflicting
  current evidence still ends in `insufficient_evidence`.

## D-028: Capture durable context as append-only classified private records

- **Status:** Accepted
- **Decision:** The skill proactively creates minimal durable records below
  `private/context/` for confirmed facts, user decisions, temporary assumptions,
  proposals, and external evidence that are likely to affect later work. Records
  are append-only, source-labelled, dated, and may supersede but never overwrite a
  prior record.
- **Why:** Important constraints and decisions should survive across chats without
  requiring a separate save instruction, but proposal text and temporary
  assumptions must not silently become approved policy.
- **Consequence:** This standing authorization covers creation of new context and
  research records only. It does not authorize saving a review, changing holdings,
  transactions, theses, targets, or policy, or overwriting any private output.
  Typed public create/save/list APIs choose collision-resistant filenames, reject
  unsafe or non-ignored targets, and verify that a superseded context record exists.

## D-029: Generalize bounded host-native perspectives for consequential reviews

- **Status:** Accepted
- **Decision:** The skill automatically selects the smallest useful set of at
  least two independent Codex subagent roles plus one later critic for supported
  analyses that are consequential, uncertain, evidence-conflicted, or materially
  bias-sensitive. Equity review retains its strict four-specialist schema. Other
  routes use a separate strict generic packet/result schema with claim-level
  evidence references, host-owned execution metadata, and validated critic input.
  Routine deterministic contributions
  remain single-threaded unless a material conflict is explicitly escalated.
- **Why:** Independent contexts can expose different evidence, risk, and
  portfolio-fit failures, while using agents indiscriminately adds cost and does
  not improve short dependent calculations.
- **Consequence:** The lead performs research and arithmetic before delegation;
  specialists do not browse, use tools, read files, or recalculate. Generic
  packets use route-specific allowlists, opaque aliases, and no inherited
  conversation history; if packet validation or packet-only isolation is
  unavailable, the workflow falls back before spawning. Each role runs once,
  followed by one critic and one synthesis, with no retry or debate loop. Agent
  artifacts remain memory-only without immediate persistence approval. Malformed
  generic results never enter critic or synthesis input, and fewer than two valid
  generic specialists forces the sequential fallback. Equity
  fallback is `deterministic_only`; non-equity same-thread fallback is
  `single_thread_sequential`. Agreement is never evidence.

## Phase 9 approval effects

The user's explicit instruction to add automatic current-source checks, reusable
private research caching, proactive durable context, and conditional multi-agent
perspectives accepts D-027 through D-029 and Phase 9 implementation. It authorizes
foreground host research plus creation of new append-only records under the
selected ignored `private/` workspace. It does not authorize staging, committing,
pushing, publication, personal installation, background monitoring, a live Python
provider, broker access, transactions, holdings changes, thesis changes, target or
policy mutation, saved-review persistence, or overwriting private output.
