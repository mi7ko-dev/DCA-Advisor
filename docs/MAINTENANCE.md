# Maintenance Guide

## Change boundary

Keep changes narrow and preserve the public/private split. Every tracked fixture,
example, report, test value, comment, and screenshot must be synthetic. Real user
state and every derivative belong below an ignored `private/` directory and must
not be copied into diagnostics, issue text, snapshots, or test failures.

Before changing a schema, formula, storage boundary, provider request, approval
gate, supported host, or license assumption, update the relevant decision and
architecture records. Do not silently reinterpret existing persisted fields.

## Safe change sequence

1. Inspect `git status`, the affected schemas, implementation, tests, and decision
   records. Do not clean or overwrite unrelated user work.
2. Add or update deterministic tests first for the changed invariant and failure
   path. Use fixed dates and synthetic decimal strings.
3. Change the smallest implementation surface. Keep calculations pure and provider
   facts separate from interpretation.
4. Regenerate all public synthetic outputs and confirm they are reproducible.
5. Review the diff manually for user-specific data, machine paths, credentials,
   private prompts, raw provider errors, unexpected language, and license notices.
6. Run the complete verification gate before requesting commit or publication.

## Version discipline

- Increment calculation or schema versions when an output's meaning or persisted
  structure changes; add migration behavior before claiming compatibility.
- Preserve Decimal arithmetic, dated sources, explicit currency, signed drift,
  cash reconciliation, and non-mutation assertions.
- Treat new dependencies as a design decision. Pin build and CI inputs where
  practical, document their purpose and license, and avoid adding a dependency for
  behavior supported safely by the standard library.
- A live provider requires a terms, authentication, retention, rate-limit, cache,
  redistribution, error-redaction, and data-flow review plus network-independent
  contract tests.
- Transaction recording, target-policy mutation, and overwrite operations require
  distinct APIs and immediate explicit approval. Analysis never grants it.

## Verification gate

```powershell
python -m compileall -q src tests tools
python tools/generate_synthetic_example.py
python tools/generate_synthetic_intelligence.py
python tools/generate_synthetic_committee.py
python tools/generate_synthetic_equity.py
git diff --exit-code -- examples
python -m unittest discover -s tests -p "test_*.py"
python tools/run_repository_checks.py --require-gitleaks
git diff --check
```

Also validate the skill with the local Codex skill validator when available. CI
uses Python 3.11, installs the source package without dependencies, regenerates all
synthetic outputs, runs the full tests, and runs the pinned Gitleaks scan. It does
not upload reports or scan artifacts.

Review `git ls-files` and `git diff --cached` before every commit. The safety tool
checks tracked index blobs and untracked public candidates, while the history scan
covers refs available in the current clone. It cannot prove that deleted remote
refs, forks, or objects unavailable to the clone are clean.

## Distribution and licensing

The supported distribution is the repository itself: a Python source package plus
the repo-local skill under `.agents/skills/steadyfolio/`. No plugin archive or
general host package is required for that supported use, and no release artifact is
currently produced.

If a future host requires a distributable artifact, build it in a temporary
directory from an explicit allowlist. Fail if its inventory contains `private/`,
`.git/`, credentials, caches, local outputs, or files outside the
allowlist. Inspect the archive, verify notices, and test a clean installation before
publication. A local build is not permission to publish.

The project license is MIT. The current implementation has no runtime third-party
dependency and contains no copied upstream code, so no third-party notice file is
required. Any future copied or adapted code needs a file-level provenance and
license review before it enters the repository.

## Deferred capabilities

Do not imply support for live market data, broker connectivity, order placement,
tax or suitability conclusions, autonomous browsing, background monitoring,
unbounded agent debate, automatic target changes, global skill installation, a
plugin bundle, or non-Codex hosts. Each needs a separately approved design,
security review, tests, and documentation.
