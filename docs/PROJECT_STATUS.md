# Project Status

## Active phase

Phase 4 - Portfolio Intelligence and Research is complete and awaiting approval to continue.

## Completed technical work

- Confirmed the project root and inspected the existing Git index and available history.
- Reconciled the public/private ignore boundary while keeping public skill locations trackable.
- Added a Git-backed repository-safety checker, synthetic tests, and a minimal-permission CI workflow.
- Added a redacted local Gitleaks workflow that scans Git history and public candidate files without scanning ignored private state.
- Added optional pre-commit and pre-push hook templates without changing local or global Git configuration.
- Shallow-cloned all six reference repositories into ignored `blueprint/` subdirectories and recorded their metadata in the local ignored reference workspace.
- Recorded each reference URL, checkout state, commit, license location, preliminary license, and relevance.
- Audited the six recorded reference commits and documented verified capabilities, calculation and test quality, privacy conflicts, scope fit, and licensing constraints in `docs/BLUEPRINT_REVIEW.md`.
- Compared adapting CoFolio, building a clean skill from reviewed concepts, and retaining CoFolio with a separate extension; selected the clean repository-owned foundation as the proposed baseline.
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
- Added a replaceable research-provider protocol and a static offline provider whose requests contain only public instrument/listing identifiers and an as-of date.
- Added validated research snapshots with source dates, retrieval times, freshness, methodology, limitations, provider terms, and cache/redistribution permissions.
- Added coverage-aware ETF metadata, holdings overlap, observed company/issuer concentration, and sector/geography/currency exposure without treating missing data as zero.
- Added compatible-series cumulative return, annualized volatility, maximum drawdown, correlation, benchmark comparison, and explicit stress-window analysis.
- Extended holding theses with approved target references, ranges, benchmarks, risks, triggers, and review dates; added evidence-separated, non-mutating review proposals.
- Added public synthetic Phase 4 inputs, structured outputs, reports, schemas, and deterministic failure/invariant tests.

## Open technical issues

- AI Finance Assistant does not grant general code-reuse permission and must remain architecture-only reference material.
- Wealthfolio and Ghostfolio are AGPL-3.0 at the repository root; main-code reuse is not recommended without an explicit later license decision.
- Local Codex remains the only first supported runtime. A future generated plugin may provide a portability path, but no general ChatGPT/plugin compatibility has been tested or claimed.
- No upstream test suite was executed during the static audit; the review distinguishes inspected test coverage from locally reproduced results.
- Hook templates are not enabled automatically because an existing local hook workflow must not be replaced without review.
- The MVP supports ETF and stock positions only, direct or inverse FX pairs only, and does not model an existing portfolio cash balance.
- Live market-data retrieval, broker connectivity, research agents, tax optimization, rebalancing sales, user interface, and host skill packaging remain outside the implemented boundary.
- No live research provider is implemented; provider-specific authentication, terms validation, rate limits, caching, and optional live integration tests remain deferred.
- Look-through data is deliberately partial, historical samples are illustrative, and all metrics are descriptive rather than predictive.
- Tax and regulatory questions remain unresolved without current jurisdiction-specific primary sources.

## Next approval gate

Phase 5 - Multi-Agent Investment Committee requires explicit approval. No approval is inferred from this file.
