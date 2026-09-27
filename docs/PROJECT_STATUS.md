# Project Status

## Active phase

Phase 6 - Final Hardening and Documentation is complete in the working tree and is
at its approval checkpoint. The Phase 6 changes are not staged, committed, pushed,
packaged, or published.

## Completed technical work

- Confirmed the project root and inspected the existing Git index and available history.
- Reconciled the public/private ignore boundary while keeping public skill locations trackable.
- Added a Git-backed repository-safety checker, synthetic tests, and a minimal-permission CI workflow.
- Added a redacted local Gitleaks workflow that scans Git history and public candidate files without scanning ignored private state.
- Added optional pre-commit and pre-push hook templates without changing local or global Git configuration.
- Defined the proposed component boundaries, host-independent Python engine, canonical skill location, private workspace boundary, JSON/Markdown persistence, domain model, financial invariants, and bounded review workflow in `docs/ARCHITECTURE.md`.
- Recorded the proposed foundation, runtime, storage, schema, committee, provenance, license, Phase 3 scope, and packaging decisions in `docs/DECISIONS.md`.
- Verified the proposed repo-local skill and future plugin portability path against current official OpenAI skill and plugin documentation; target-host compatibility remains something to test, not assume.
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

The local interpreter is Python 3.9.7 32-bit; Python 3.11, Ruff, and Pyright are not
installed locally. Therefore a clean install on the supported Python version and
those optional static tools were unavailable locally. CI is configured to install
and import the source package on Python 3.11, but that updated workflow cannot run
until an authorized commit and push. No release artifact was built because the
supported repo-local distribution does not require one.

History coverage includes only objects and refs available in this clone. It cannot
attest to deleted remote refs, unavailable objects, forks, or private systems.

## Open technical issues

- Local Codex remains the only supported host. Discovery is verified in the current
  repository session, but a clean-machine host test, global installation, generated
  plugin, and general ChatGPT compatibility have not been tested or claimed.
- No upstream test suite was executed during the static audit; the review distinguishes inspected test coverage from locally reproduced results.
- Hook templates are not enabled automatically because an existing local hook workflow must not be replaced without review.
- The MVP supports ETF and stock positions only, direct or inverse FX pairs only, and does not model an existing portfolio cash balance.
- Live market-data retrieval, broker connectivity, true independent research agents, tax optimization, rebalancing sales, user interface, and plugin packaging remain outside the implemented boundary.
- No live research provider is implemented; provider-specific authentication, terms validation, rate limits, caching, and optional live integration tests remain deferred.
- Look-through data is deliberately partial, historical samples are illustrative, and all metrics are descriptive rather than predictive.
- Tax and regulatory questions remain unresolved without current jurisdiction-specific primary sources.

## Next approval gate

Phase 6 is the final approved project phase. Any commit, push, package publication,
live-provider work, broker integration, transaction recording, policy mutation, or
new product scope requires a separate explicit instruction. No approval is inferred
from this file.
