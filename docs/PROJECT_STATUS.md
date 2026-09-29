# Project Status

## Active phase

Phase 9 current-source research, append-only private cache/context, and bounded
multi-agent review expansion plus the automated-review remediations are implemented
and verified as development version `0.3.1`. The owner explicitly authorized this
version generation, personal Codex reinstall, commit, and feature-branch push on
2026-09-29. Version `0.3.1` is installed locally through the development
cachebuster `0.3.1+codex.20260929205739` and has a verified local archive;
this revision is committed to the Phase 9 feature branch but is not merged,
published, or declared released. The latest published release remains `0.2.1`.

## Completed technical work

- Confirmed the project root and inspected the existing Git index and available history.
- Reconciled the public/private ignore boundary while keeping public skill locations trackable.
- Added a Git-backed repository-safety checker, synthetic tests, and a minimal-permission CI workflow.
- Added a redacted local Gitleaks workflow that scans Git history and public candidate files without scanning ignored private state.
- Added optional pre-commit and pre-push hook templates without changing local or global Git configuration.
- Defined the proposed component boundaries, host-independent Python engine, canonical skill location, private workspace boundary, JSON/Markdown persistence, domain model, financial invariants, and bounded review workflow in `docs/ARCHITECTURE.md`.
- Recorded the proposed foundation, runtime, storage, schema, committee, provenance, license, Phase 3 scope, and packaging decisions in `docs/DECISIONS.md`.
- Verified the proposed repo-local skill and future plugin portability path against current official OpenAI skill and plugin documentation; target-host compatibility remains something to test, not assume.
- Added a self-contained `steadyfolio` Codex plugin under `plugins/steadyfolio/`
  and repo-local `steadyfolio-local` marketplace manifest generated from a literal
  public-file allowlist.
- Added exact plugin-inventory, canonical-skill, isolated-runtime, manifest, and
  reproducibility tests plus a Python 3.11 CI smoke installation.
- Addressed repository-safety review findings by restoring legacy private-path patterns, scanning staged index blobs rather than edited working-tree copies, and forcing the pinned Gitleaks installer to replace and verify its local executable.
- Accepted the Phase 2 architecture and decision record as the Phase 3 baseline.
- Implemented a dependency-free Python 3.11 portfolio core with immutable domain models, strict validation, Decimal arithmetic, dated prices and FX rates, current weights, signed drift, weighted fees, and direct-concentration metrics.
- Implemented simple target-weight and drift-aware buy-only contribution planning with whole or fractional quantities, trading increments, minimum trades, fixed and variable fees, upward fee rounding, downward quantity rounding, and exact cash conservation.
- Added safe private JSON and Markdown persistence with validation before write, path and symlink checks, atomic creation, and non-overwrite defaults.
- Added public JSON Schemas, fully synthetic examples, structured result fixtures, an English contribution report, and a reproducible EUR 400 scenario generator.
- Added deterministic tests covering portfolio analysis, missing prices and FX, multi-currency valuation, invalid inputs, whole and fractional trading, fees, residual cash, contribution sizes, non-mutation, persistence safety, and repository safety.
- Added a replaceable research-provider protocol and a static offline provider whose requests contain only public instrument/listing identifiers, explicitly referenced public evidence-source identifiers, and an as-of date.
- Added validated research snapshots with source dates, retrieval times, freshness, methodology, limitations, provider terms, and cache/redistribution permissions.
- Added coverage-aware ETF metadata, holdings overlap, observed company/issuer concentration, and sector/geography/currency exposure without treating missing data as zero.
- Added compatible-series cumulative return, annualized volatility, maximum drawdown, correlation, benchmark comparison, and explicit stress-window analysis.
- Extended holding theses with approved target references, ranges, benchmarks, risks, triggers, and review dates; added evidence-separated, non-mutating review proposals.
- Added public synthetic Phase 4 inputs, structured outputs, reports, schemas, and deterministic failure/invariant tests.
- Added the canonical repo-local SteadyFolio skill with clear discovery metadata, bounded workflow instructions, approval gates, and progressively loaded references.
- Added deterministic routing for contribution, portfolio-review, overlap-review, thesis-review, and clarification paths.
- Added structured committee results that separate facts, sources/dates/limitations, assumptions, specialist interpretations, disagreements, synthesis, approval requirements, and the actual execution trace.
- Added selective sequential review lenses with at most one research pass, one critic pass, one revision, and no live external calls; the output does not claim independent agent verification.
- Added non-mutating committee-review persistence under `private/reviews/` and explicit approval boundaries for transactions and target or policy changes.
- Added six fully synthetic end-to-end demonstrations covering EUR 400 contribution, portfolio review, ETF thesis review, partial overlap, residual drift, and missing/stale evidence with contradictory conclusions.
- Validated the public skill structure with the bundled skill validator and added routing, integration, privacy, output, and repository-safety coverage.
- Hardened provider-failure traces so a failed bounded attempt is recorded while
  raw exception details remain absent from the structured result.
- Added storage tests for symlinked output directories and target files, provider
  failure redaction and call bounds, and portable repo-local skill structure.
- Extended CI to use Python 3.11, install and import the source package, compile the
  Python surface, regenerate every synthetic output, enforce reproducibility, and
  run a checksum-pinned Gitleaks scan without uploading artifacts.
- Added final setup, synthetic walkthrough, private-state operation, provider-flow,
  troubleshooting, maintenance, verification, distribution, and licensing guides.
- Confirmed in the current Codex repository session that the repo-local
  `steadyfolio` skill is discovered; the skill also passes the bundled validator.
- Re-reviewed the public index, current staged state, available Git history,
  authored language, generated outputs, dependency boundary, license, and absence
  of required third-party notices.
- Addressed the consolidated automated review findings across calculation,
  validation, persistence, reporting, research, and committee boundaries. The
  hardening rejects ambiguous market and evidence inputs, preserves approved
  allocation history, validates derived outputs before saving, and treats absent
  coverage as insufficient evidence.
- Addressed follow-up review findings by fingerprinting selected listing
  constraints, rejecting contribution amounts joined to identifier characters,
  and versioning the three-observation research contract as schema `1.1` with
  explicit read compatibility for schema `1.0`.
- Added strict stock identity matching across recorded instrument name, ISIN, and
  optional listing ID, MIC, ticker, and trading currency; duplicate non-null ISINs
  can no longer create separate economic instruments.
- Added the offline `equity_quality_v1` model with a positive-free-cash-flow hard
  screen, eight disclosed criteria, unavailable-data denominator handling,
  completeness gates, and a separate circle-of-competence result.
- Added hierarchical DCF, reverse-DCF, and forward-P/E valuation anchors with
  explicit margin of safety, conflict detection without averaging, and optional
  owner-earnings evidence for high-CapEx cases.
- Added a configurable private portfolio-policy contract for direct-weight,
  fragmentation, satellite, and named factor-group checks while explicitly
  limiting the current denominator to invested positions.
- Added deterministic committee routing for individual-equity review, public JSON
  contracts, private non-overwriting persistence, synthetic examples and reports,
  documentation, skill routing, and CI regeneration.
- Added immutable versioned input packets for evidence, business-quality,
  valuation, portfolio-risk, and critic roles, plus strict versioned specialist
  outputs with claim-level evidence references and non-sensitive execution metadata.
- Added the Codex-native Phase 8 skill workflow: four isolated specialist threads,
  one isolated critic thread, one lead synthesis, no retries, and deterministic
  engine precedence. Contribution and other routes do not start these agents.
- Added CommitteeResult `2.0` multi-agent envelopes while retaining deterministic
  EquityReviewResult `1.0` and CommitteeResult `1.1` compatibility.
- Added fail-closed handling for malformed output, unknown evidence references,
  unsupported claims, timeouts, unavailable runtimes, contradictions, partial
  failures, and explicit deterministic-only fallback.
- Added network-free in-memory backend tests, a synthetic contract demonstration,
  and a defect-code eval that compares detected defects rather than agent votes.
- Documented hosted Codex processing, role-minimal data transfer, token and latency
  costs, approval boundaries, trace redaction, and inherited-tool limitations.
- Added automatic one-pass host-native research for material time-sensitive facts,
  with primary-source preference, explicit dates and limitations, and no real-time
  claim.
- Added append-only private research caching and classified durable context under
  `private/`, with source-term checks, cache freshness decisions, and no overwrite
  or policy-mutation authority.
- Added automatic bounded Codex-native specialist perspectives for consequential,
  uncertain, conflicting, or bias-sensitive non-equity reviews while retaining the
  strict Phase 8 equity contract and routine-contribution exclusion.

## Version 0.3.1 review-remediation verification record

Verification completed on 2026-09-30 with these results:

- Added typed public create/save/list APIs for append-only research-cache and
  durable-context records. The writers validate schemas and reuse ignored-target,
  symlink, atomic, and exclusive-create safeguards; context corrections must link
  an existing prior record.
- Added version `1.0` generic non-equity packet and result schemas, content-bound
  packet IDs, exact-field parsers, evidence-reference validation, host-owned
  execution metadata, and a critic builder that accepts only validated specialist
  results.
- Clarified that routine contributions stop instead of browsing for missing or
  stale required inputs, and that verified evidence may remain in memory when its
  terms allow current use but prohibit retention.
- Python compilation passed for `src/`, `tests/`, and `tools/`; all 195 unit,
  integration, privacy, invariant, release, plugin, skill, equity, multi-agent,
  private-record, generic-agent, and repository-safety tests passed.
- All five synthetic generators reproduced the tracked example tree without a
  diff. The canonical and bundled skills reported `Skill is valid!`, the plugin
  reported `Plugin validation passed`, and the bundled runtime imported with an
  explicit Python 3.11 `src` path.
- A 95-file allowlisted marketplace reproduced the tracked plugin mirror exactly.
  Repository safety passed 13 ignored-path and 12 public-path expectations against
  213 tracked files; Gitleaks 8.30.1 passed for available history and 213 current
  public candidate files.
- The deterministic `steadyfolio-0.3.1.zip` archive was generated outside the
  repository with SHA-256
  `5ccfb5a8b6340ecda03ed23224ecc091f2e5c4a2ecc54b88960a1e8388f3e706`.
- The local `steadyfolio-local` marketplace installed and enabled development
  version `0.3.1+codex.20260929205739`; its code, skill, and documentation matched
  canonical version `0.3.1`, whose manifest was restored before commit. No
  publication, merge, transaction, portfolio mutation, private overwrite, or real
  user-data operation was performed.

## Phase 9 local verification record (historical pre-commit checkpoint)

Verification on 2026-09-29 completed with these results:

- Python compilation passed for `src/`, `tests/`, and `tools/`; all 183 unit,
  integration, privacy, invariant, release, plugin, skill, equity, multi-agent,
  and repository-safety tests passed.
- All five synthetic generators reproduced the tracked example tree without a
  diff.
- The canonical and bundled skills reported `Skill is valid!`; the tracked plugin
  reported `Plugin validation passed`; and its bundled runtime imported with an
  explicit Python 3.11 `src` path and no ambient package assumption.
- An 88-file allowlisted marketplace was built outside the repository, validated,
  copied to the tracked mirror, and reproduced exactly by the plugin-package tests.
- Repository safety passed 13 ignored-path expectations and 12 public-path
  expectations against 193 tracked files. Gitleaks 8.30.1 passed for available Git
  history and 197 current public candidate files.
- No personal plugin reinstall, release archive, stage, commit, push, publication,
  transaction, holdings change, thesis change, policy mutation, private overwrite,
  or real user-data operation was performed.

## Release 0.2.1 local verification record

Verification on 2026-09-29 completed with these results:

- The Python package, plugin manifest, generated plugin README, operations docs,
  and tracked plugin mirror use canonical version `0.2.1` without a cache-buster.
- 181 unit, integration, privacy, invariant, release-archive, plugin-package,
  skill-structure, equity-review, and repository-safety tests passed with zero
  failures. Python compilation passed for `src/`, `tests/`, and `tools/`.
- All five synthetic generators ran twice and reproduced the complete example tree
  byte for byte with SHA-256 tree digest
  `281bc6b8a55f08927ac76d57f549376df1167c3ac90f8e7e19ab122a1f5e2474`.
- An 86-file plugin marketplace was built outside the repository from the public
  allowlist, validated, inspected for links and sensitive markers, imported in
  isolation, and matched to the tracked mirror byte for byte.
- Two independently built `steadyfolio-0.2.1.zip` archives were identical and had
  SHA-256 `f8dbf8a17a0e2037cc0fcafd3555aed497f7e977353154bddf09a6c052973dd7`.
  A clean extracted copy passed plugin, skill, manifest, and isolated-runtime
  validation. The archive remains outside the repository and is not published.
- Codex reported the release plugin as installed and enabled after the official
  cache-buster reinstall flow. The tracked manifest was restored to canonical
  `0.2.1`, and the installed runtime imported without creating bytecode.
- Repository safety passed 13 ignored-path expectations and 12 public-path
  expectations against 191 tracked files. Gitleaks 8.30.1 passed for available Git
  history and 193 current public candidate files.
- The local host exposes Python 3.9.7 only. The supported Python 3.11 CI job is
  configured but cannot run until the changes are committed and pushed; no local
  Python installation was modified for this release.

## Phase 8 local verification record

Verification on 2026-09-29 completed with these results:

- 174 unit, integration, privacy, invariant, eval, repository-safety,
  skill-structure, plugin-package, equity-review, and portfolio-policy tests passed
  with zero skips.
- Python compilation passed for `src/`, `tests/`, and `tools/`. All five synthetic
  generators reproduced 26 public example files byte for byte on a second run.
- A fresh 86-file plugin marketplace was built outside the repository from the
  explicit public allowlist, inspected for links, forbidden paths, credentials,
  local paths, private markers, and approval text, then copied to the tracked
  mirror and compared byte for byte.
- The bundled plugin validator reported `Plugin validation passed`; both canonical
  and bundled skill validators reported `Skill is valid!`; and the temporary
  bundled runtime imported with repository `src/` excluded from `PYTHONPATH`.
- Repository safety passed 13 ignored-path expectations and 12 public-path
  expectations against 170 tracked files. Gitleaks 8.30.1 passed for available Git
  history and 191 current public candidate files. `git diff --check` passed.
- A real Codex-host synthetic smoke started four isolated specialist threads and a
  later isolated critic thread. All four specialist content outputs satisfied the
  content-only contract. The critic found the intended portfolio evidence gap but
  returned an unsupported conclusion enum, so the lead rejected it without retry;
  this demonstrated the documented `partial_agent_failure` behavior rather than a
  false complete review. No raw response or private output was persisted.
- No API key, paid model API call, external dependency, plugin reinstall, stage,
  commit, push, publication, transaction, or policy mutation was performed.

## Phase 6 plugin packaging local verification record (historical)

Verification on 2026-09-28 completed with these results:

- The allowlist builder reproduced an exact 76-file marketplace containing the
  `steadyfolio` plugin, canonical skill, deterministic engine, schemas, operating
  documentation, and synthetic examples.
- The bundled plugin validator reported `Plugin validation passed`, and both the
  canonical and bundled skill validators reported `Skill is valid!`.
- The bundled runtime imported with repository `src/` excluded from `PYTHONPATH`.
- 144 unit, integration, privacy, invariant, repository-safety, skill-structure,
  plugin-package, equity-review, and portfolio-policy tests passed with zero skips.
- Python compilation passed for `src/`, `tests/`, and `tools/`, and every synthetic
  generator reproduced its committed output.
- Repository safety passed 13 ignored-path expectations and 12 public-path
  expectations. Gitleaks 8.30.1 passed for available history and 170 current public
  candidate files.
- Bundle searches found no local user name, machine path, approval token, private
  key marker, or credential filename. The patch whitespace check passed.
- The local Python launcher exposes only Python 3.9.7. The supported Python 3.11
  clean `pip --target` smoke installation is configured in CI and awaits an
  authorized commit and push; no personal Codex installation was performed.

## Phase 7 local verification record

Verification on 2026-09-28 completed with these results:

- 133 unit, integration, privacy, invariant, repository-safety, skill-structure,
  equity-review, and portfolio-policy tests passed with zero skips.
- Python compilation passed for `src/`, `tests/`, and `tools/`.
- All public synthetic generators reproduced the examples byte for byte.
- The bundled skill validator reported `Skill is valid!`.
- Repository safety passed 13 ignored-path expectations and 12 public-path
  expectations against 73 tracked files and 92 current public candidate files.
- Gitleaks 8.30.1 passed for available Git history and all 92 public candidates.
- Searches found no copied personal stock-skill terms, local machine paths, or
  Cyrillic text in project-authored public files, and the patch whitespace check
  passed.
- Ruff and Pyright were unavailable locally. The local interpreter remains Python
  3.9.7, while the supported runtime and CI target remain Python 3.11 or newer.

## Phase 6 local verification record

Verification on 2026-09-27 completed with these results:

- 109 unit, integration, privacy, invariant, repository-safety, and skill-structure
  tests passed with zero skips.
- Python compilation passed for `src/`, `tests/`, and `tools/`.
- All three synthetic generators reproduced the working-tree examples byte for byte
  on a second run.
- The bundled skill validator reported `Skill is valid!`.
- Repository safety passed 15 ignored-path expectations and 12 public-path
  expectations against both the 70-file current Git index and a temporary 74-file
  staged-equivalent index containing every current public working-tree change.
- Gitleaks 8.30.1 passed for all history reachable in the non-shallow local clone
  and 74 current public candidate files. The clone contained 24 reachable commits.
- The staged diff was empty, no tracked symlink was present, and the manual
  authored-language and machine/user-identifier
  searches returned no finding, and the patch whitespace check passed.

The earlier local verification used Python 3.9.7 32-bit; Python 3.11, Ruff, and
Pyright were not installed at that checkpoint. The supported-version CI smoke and
optional static tools remained deferred. Release `0.2.1` supersedes the earlier
statement that no local release archive would be built; its archive is generated
outside the repository and is not published without separate authorization.

History coverage includes only objects and refs available in this clone. It cannot
attest to deleted remote refs, unavailable objects, forks, or private systems.

## Open technical issues

- Local Codex remains the only supported host. Repo-local discovery, the generated
  plugin structure, and a personal-profile install are verified, but a clean-machine
  cross-platform host test and general ChatGPT compatibility have not been tested
  or claimed.
- No upstream test suite was executed during the static audit; the review distinguishes inspected test coverage from locally reproduced results.
- Hook templates are not enabled automatically because an existing local hook workflow must not be replaced without review.
- The MVP supports ETF and stock positions only, direct or inverse FX pairs only, and does not model an existing portfolio cash balance.
- A Python live market-data provider, guaranteed real-time feed, broker
  connectivity, tax optimization, rebalancing sales, background monitoring, and a
  user interface remain outside the implemented boundary.
- Host-native web research depends on the selected Codex host. No provider-specific
  authentication, rate-limit integration, raw-response cache, or optional live
  provider integration test is implemented.
- Generic non-equity packet, result, and critic contracts are validated by Python,
  but the live Codex spawning step remains host-orchestrated rather than a Python
  model-service adapter or persisted committee envelope.
- Look-through data is deliberately partial, historical samples are illustrative, and all metrics are descriptive rather than predictive.
- Tax and regulatory questions remain unresolved without current jurisdiction-specific primary sources.

## Next approval gate

The authorized version `0.3.1` generation, local install, commit, and feature-branch
push are complete. Merge, release declaration, archive or package publication,
additional commit or push, Python live-provider work, broker integration, tax
adapter, transaction recording, holdings/thesis/target or policy mutation, private
overwrite, background monitoring, or new product scope requires a separate explicit
instruction. No further approval is inferred from this file.
