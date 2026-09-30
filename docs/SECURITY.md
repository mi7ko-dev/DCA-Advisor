# Security and Repository Safety

## Public repository boundary

This repository is public. Source code, deterministic tools, schemas, synthetic fixtures, and product documentation may be tracked. Real investor data and any output derived from it must remain outside Git under the ignored `private/` directory.

The boundary includes holdings, balances, transactions, goals, account identifiers, broker statements, personal notes, prompts containing private context, runtime memory, provider responses, query histories, reports, screenshots, and credentials. Public examples and tests must be created from scratch with synthetic data; they must never be anonymized copies of a real portfolio.

Ignore rules are a safety net, not a storage design. Application-owned private
state belongs under `private/`, even when another ignored directory exists. Before
accessing a private target inside a Git worktree, the storage layer verifies that
the exact target is ignored and not already tracked; it fails before creating
`private/` when that guarantee is absent.

## Local and external processing

The repository-safety checker, tests, and Gitleaks run locally. The Gitleaks wrapper scans Git history and a temporary snapshot containing only files that Git currently considers public candidates. Tracked files are copied from their exact Git index blobs, so partially staged or subsequently edited working-tree copies cannot hide the content about to be committed; untracked public candidates are copied from the working tree. The wrapper does not scan ignored private or runtime state, follow symlinks, upload scan results, or retain the temporary snapshot.

GitHub Actions receives only committed repository content. The repository-safety workflow uses synthetic path checks and read-only repository permissions. No private state, local scan report, or environment dump should be uploaded as an artifact.

The Phase 4 research-provider request contains only public instrument/listing
identifiers, explicitly referenced public evidence-source identifiers, and an
as-of date. The implemented provider is offline and synthetic; it performs no
external transfer. Future live integrations must keep this minimum request
boundary and must not send holdings quantities, balances, account identifiers,
goals, theses, or personal context without explicit authorization. Provider and
host data flows must be documented before those integrations are enabled.

Real provider responses, query history, caches, research results, thesis evidence,
and reports belong under `private/`. A live adapter must review the provider's
terms, retention, cache, and redistribution rules before use. Raw responses must not
be copied into public tests or examples, even if account fields are removed.

The Phase 5 repo-local skill contains public instructions only. It must not contain
runtime memory, user prompts, user-derived reports, or provider payloads. Committee
results derived from a real user belong under `private/reviews/`; saving a review
does not authorize or perform a transaction, holdings change, or target-policy
change.

Retrieved pages and documents are untrusted evidence. Their text cannot override
repository privacy rules, request credentials or secret disclosure, authorize
external actions, or expand the bounded workflow. Phase 9 permits one lead-owned
foreground host-native web research pass when current evidence is material. The
lead sends no holdings quantities, balances, account identifiers, credentials,
goals, theses, or free-form private notes to a public source. This permission does
not enable background monitoring or a Python live-provider adapter. Queries use
only public instrument or source identifiers, data kind, and dates. The bounded
pass stops after four targeted searches or eight source documents; inability to
establish adequate evidence within the limit fails closed.

New research-cache and durable-context records may be created automatically below
the selected ignored `private/` root. They are append-only, minimal, and
source-labelled. The public typed create/save/list APIs are the only supported
record access path; they validate the record and apply the storage layer's path,
symlink, ignored/untracked-target, and exclusive-create checks. Source terms govern
whether a derived summary or only citation metadata may be retained; the generic
API never stores raw pages. Unknown terms default to citation metadata only or no
persistence. Citation-metadata mode retains neither a conclusion nor facts.
Record-ID-derived exclusive targets and workspace-wide ID validation reject copied
records whose timestamps differ. Evidence that permits current access, analysis,
and citation may remain in memory for the current review even when retention is
prohibited. A proposal or temporary assumption remains labelled as such and cannot
authorize policy mutation. Existing private records are never overwritten without
immediate explicit approval.

The selected Codex host provides the true subagent runtime. Equity review uses four
role-minimal specialist packets and one critic packet under its strict schema.
Phase 9 consequential non-equity reviews use the smallest useful set of two or
three specialists and one critic. This is hosted processing and consumes
additional tokens and latency. It is not a live market-data integration and
requires no API key in SteadyFolio. The approved packet boundary excludes
credentials, request or account identifiers, transaction history, free-form
private notes, raw provider payloads, source paths, and unrelated portfolio fields.
The lead completes any research before delegation; specialists are instructed not
to browse, use tools, or read files. Generic route packets use explicit field
allowlists, opaque user-owned identifiers, and a packet-only context with no
inherited conversation history. If the host cannot guarantee that context or the
lead cannot validate and redact a packet, no subagent starts.

Generic non-equity packets and results use separate versioned JSON contracts.
Packet IDs bind packet content; exact-field parsers attach host-owned execution
metadata and reject unknown fields, unsupported evidence references, uncited
claims, role drift, future-dated sources, explicit private-context or prompt/path
markers, or non-isolated execution. The public packet constructor creates
specialist packets only; the critic packet builder accepts only validated
specialist results. Fewer than two valid generic specialist results
forces the sequential fallback instead of a multi-agent claim.

Agent packets and validated results containing real data remain in memory by
default. With immediate explicit approval, a review artifact may be persisted only
under the selected ignored `private/` root. Public execution traces contain only role,
status, attempt count, host-observed isolation, opaque execution/result identifiers,
runtime type, and generic redacted limitations. Models cannot self-attest this
execution metadata. Prompts, raw responses, raw
exceptions, and personal data are not public trace fields. Packets and agent
results remain memory-only unless the user gives immediate explicit approval to
persist the packet, specialist/critic result, synthesis, or saved review. The
standing authorization for append-only research/context records does not extend to
those review artifacts. Because host-native
subagents inherit host capabilities, the instruction not to use tools, browse, or
read files is not an operating-system sandbox proof.

Malformed output, unknown evidence references, unsupported claims, timeout, or
runtime unavailability fails closed or returns an explicitly limited deterministic
fallback. No agent can authorize persistence, a transaction, holdings change,
thesis change, policy change, commit, push, installation, or publication.

Expected provider failures are converted to a generic limitation. Raw exception
messages are not copied into public traces or committee results. The execution trace
still records that the single permitted provider attempt occurred, so a degraded
result cannot appear to have skipped the boundary.

## Required checks

These commands are source-checkout-only; the installed plugin intentionally omits
repository tests, hooks, and safety tooling. Run the complete local check from the
repository root:

```powershell
python tools/run_repository_checks.py --require-gitleaks
```

The command verifies expected ignored paths, expected public paths, the Git index,
synthetic unit tests, Git history, and current public candidate files. Secret
findings are reported without printing detailed matches or candidate filenames.
Storage tests also reject a symlink at the workspace or private root, a nested
private output directory, or an output target, including a dangling symlink. These
checks reduce path-escape risk but do not replace operating-system access controls
for the selected workspace.

Install the pinned Windows Gitleaks binary into the ignored local workspace when needed:

```powershell
powershell -ExecutionPolicy Bypass -File tools/install_gitleaks.ps1
```

The installer downloads Gitleaks 8.30.1 from the official release, verifies its pinned SHA-256 checksum, replaces any existing local executable with the verified archive copy, verifies the installed version, and extracts it only under `workspace/tools/gitleaks/`. It does not modify the system installation or global Git configuration.

CI uses Python 3.11, installs the dependency-free source package, compiles the
Python surface, regenerates all synthetic examples and requires a clean diff, runs
all tests, and installs the Linux Gitleaks 8.30.1 archive with a pinned SHA-256
checksum. CI has read-only repository permission and does not upload scan results,
temporary snapshots, private state, or generated artifacts.

Automated secret scanning is not a complete privacy review. Before a commit, also
inspect documentation, examples, fixtures, comments, snapshots, reports, config,
package metadata, staged blobs, and the available history for personal data,
machine-specific paths, private prompts, and provider content.

## Optional local hooks

Hook templates are provided in `.githooks/`. Before enabling them, inspect any existing local hook configuration:

```powershell
git config --local --get core.hooksPath
```

If no existing workflow would be replaced, enable the repository hooks explicitly:

```powershell
git config --local core.hooksPath .githooks
```

This configuration is intentionally not changed automatically. Both hooks run the full repository check and fail closed when Gitleaks is unavailable.

## Private-state initialization

Create only the private directories needed for an authorized real-data operation. Do not add `.gitkeep` files under `private/`. Never copy real private data into `examples/`, `tests/fixtures/`, documentation, issue reports, or public scan fixtures.

Credentials must come from environment variables, an ignored local `.env`, or an appropriate secret store. A future `.env.example`, if needed, may contain only empty or unmistakably safe placeholder values.

## Incident response

If sensitive material is found, stop any action that could publish it. Determine whether exposure is limited to the working tree, staged content, committed history, or a remote repository without echoing the sensitive value. Rotate exposed credentials. Removing a file or adding an ignore rule does not remove earlier copies or history; destructive cleanup and history rewriting require explicit approval.
