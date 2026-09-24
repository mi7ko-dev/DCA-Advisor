# Project Status

## Active phase

Phase 2 - Architecture and Foundation Decision is complete and awaiting approval.

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

## Open technical issues

- AI Finance Assistant does not grant general code-reuse permission and must remain architecture-only reference material.
- Wealthfolio and Ghostfolio are AGPL-3.0 at the repository root; main-code reuse is not recommended without an explicit later license decision.
- The proposed MIT license and all Phase 2 architecture decisions remain pending explicit user approval.
- Local Codex is the only first supported runtime. A future generated plugin may provide a portability path, but no general ChatGPT/plugin compatibility has been tested or claimed.
- No upstream test suite was executed during the static audit; the review distinguishes inspected test coverage from locally reproduced results.
- Hook templates are not enabled automatically because an existing local hook workflow must not be replaced without review.

## Next approval gate

Phase 3 - Core MVP Implementation requires explicit approval of the Phase 2 architecture and scope. No approval is inferred from this file.
