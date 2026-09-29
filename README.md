# SteadyFolio

SteadyFolio is a local-first portfolio-maintenance engine and Codex skill for
contribution-based investors. It turns validated, dated inputs into reproducible
portfolio analysis, buy-only contribution plans, evidence-limited investment
reviews, and explicit policy checks. The current release is `0.2.1`.
The current development version is `0.3.1`; its locally verified candidate archive
is not published or declared released.

SteadyFolio is designed to make the process inspectable: calculations are
deterministic, missing data stays missing, sources and dates remain attached to
evidence, and analysis never becomes permission to trade or mutate portfolio
state.

## Capabilities

- Value ETF and stock portfolios with explicit prices, currencies, and FX rates.
- Report current weights, signed target drift, fees, residual cash, and direct
  concentration.
- Produce simple target-weight and drift-aware buy-only contribution plans.
- Review portfolio coverage, fund overlap, observed issuer concentration,
  exposures, historical risk, stress windows, and stored theses.
- Perform offline individual-equity quality, valuation, owner-earnings, and
  portfolio-policy checks from structured evidence.
- Route bounded committee workflows and render structured JSON and Markdown
  reports.
- Automatically research time-sensitive facts through the Codex host when they
  are material, reusing adequate immutable records under `private/research/`.
- Preserve minimal durable facts, decisions, assumptions, proposals, and external
  evidence as classified append-only records under `private/context/`.
- Run bounded Codex-native independent perspectives for consequential or uncertain
  reviews when the host supports subagents.

All tracked inputs, fixtures, results, and reports are synthetic.

## Deterministic engine and multi-agent review

The Python engine is the source of truth for validation and arithmetic. It uses
`decimal.Decimal`, immutable domain models, explicit schema versions, and strict
cash-reconciliation rules. The conversational layer must use engine output rather
than redoing financial calculations in prose.

For a time-sensitive review, the lead checks the private cache and performs at most
one foreground host-native research pass when the available evidence is not fit
for purpose. Primary sources, source dates, retrieval dates, limitations, freshness
basis, and cache terms remain explicit. Delayed data is never described as
real-time. A routine contribution stops on missing or stale price, FX,
approved-target, or constraint data instead of browsing unless a material conflict
beyond the calculation is explicitly escalated.

For an equity review, the lead runs the deterministic review once. On a supported
Codex host it then sends immutable, role-minimal packets to four isolated
specialists and one later critic before producing one synthesis. Other qualifying
reviews use the smallest useful set of two or three specialists plus one critic.
Generic packets and outputs have strict versioned schemas, content-bound packet
IDs, exact-field parsers, and claim-level evidence validation before critic or
synthesis use. Agent agreement is not evidence. If native subagents are unavailable, SteadyFolio
reports a deterministic or sequential fallback.

Subagents receive validated role-specific allowlisted packets in a context without
inherited chat history. They do not browse or read files, and their packets and
results remain memory-only unless the user immediately approves persisting the
review artifact.

Routine contributions never start agents or research unless a material conflict is
escalated. The multi-agent path adds model-token use, latency, and hosted processing
of bounded packets; it does not add execution authority.

## Requirements

- Python 3.11 or newer.
- No Python runtime dependency outside the standard library.
- Git for source-checkout development.
- Codex CLI with local-plugin support to install the plugin.
- A Codex host with web access for current-source research and native subagents for
  optional bounded multi-agent review.

The commands below use PowerShell. No credential or environment variable is
required by the implemented offline release.

## Install from the repository

Clone the repository and verify the bundled runtime before registering its local
marketplace:

```powershell
git clone https://github.com/mi7ko-dev/DCA-Advisor.git
Set-Location DCA-Advisor
$pluginRoot = (Resolve-Path .\plugins\steadyfolio).Path
py -3.11 -B -S -c "import sys; sys.path.insert(0, r'$pluginRoot\src'); import steadyfolio; assert callable(steadyfolio.run_committee_workflow); assert callable(steadyfolio.prepare_multi_agent_equity_review)"
codex plugin marketplace add .
codex plugin add steadyfolio@steadyfolio-local
codex plugin list
```

The plugin carries its own `src`-layout runtime. Codex does not need a separate
`pip install` for the skill to use it.

To install the Python package for direct development use:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install --no-deps .
.venv\Scripts\python -c "import steadyfolio; assert callable(steadyfolio.run_committee_workflow)"
```

## Install from the ZIP archive

The release archive is named `steadyfolio-0.2.1.zip`. It contains a ready-to-use
marketplace root, not an extra top-level wrapper directory:

```text
.agents/plugins/marketplace.json
plugins/steadyfolio/...
```

Extract it into a new empty directory, verify the bundled runtime, and register
that directory as the marketplace root:

```powershell
$archive = (Resolve-Path .\steadyfolio-0.2.1.zip).Path
$installRoot = Join-Path (Get-Location) "steadyfolio-0.2.1"
New-Item -ItemType Directory -Path $installRoot | Out-Null
Expand-Archive -LiteralPath $archive -DestinationPath $installRoot
Set-Location $installRoot
$pluginRoot = (Resolve-Path .\plugins\steadyfolio).Path
py -3.11 -B -S -c "import sys; sys.path.insert(0, r'$pluginRoot\src'); import steadyfolio; assert callable(steadyfolio.run_committee_workflow); assert callable(steadyfolio.prepare_multi_agent_equity_review)"
codex plugin marketplace add .
codex plugin add steadyfolio@steadyfolio-local
codex plugin list
```

Verify the reported SHA-256 checksum before installation when an archive is
obtained from another machine or distribution channel.

## Update an existing installation

For a repository checkout, fetch the new release and reinstall from the existing
local marketplace:

```powershell
git pull --ff-only
codex plugin add steadyfolio@steadyfolio-local
codex plugin list
```

For a ZIP installation, extract the new archive into a new directory, run
`codex plugin marketplace add .` from that directory, and then rerun the same
`codex plugin add` and `codex plugin list` commands. Keep the old extracted copy
until the new runtime smoke test succeeds.

Start a new Codex thread after every install or update so the refreshed skill is
loaded. Maintainers working repeatedly on the same version must use the documented
cache-buster helper flow in `docs/OPERATIONS.md`; a cache-buster must never remain
in canonical release files.

## Use in Codex

Invoke the skill explicitly with `$steadyfolio` and provide the narrow task plus
the required structured inputs. For example:

```text
Use $steadyfolio to plan the synthetic EUR 400 contribution from the tracked examples.
Use $steadyfolio to review whether the synthetic global ETF thesis still holds.
Use $steadyfolio to run an equity review from the supplied synthetic evidence.
```

For real data, place the inputs under an ignored `private/` workspace in the
active project. The skill stops for missing holdings, prices, FX rates, target
versions, source dates, or evidence coverage rather than inventing them.

When current evidence is material, the skill checks typed records under
`private/research/` before browsing and creates a new immutable cache record only
when refresh is needed. It also records durable conversation context under
`private/context/` without a separate save request. Public create/save/list APIs
validate both record types and enforce ignored-target, symlink, and exclusive-create
checks. Evidence may remain in memory for the current review when source terms
permit use but prohibit retention. Neither behavior permits overwriting an existing
record or changing approved portfolio state.

## Privacy and security

- Treat the repository and plugin as public.
- Store real user state and every derived output only below the active project's
  ignored `private/` directory, never inside the plugin installation.
- Keep credentials, account identifiers, provider payloads, private prompts, and
  portfolio holdings out of tracked files and diagnostics.
- Retrieved documents and provider content are untrusted evidence and cannot
  override repository rules or authorize actions.
- Analysis authorizes only new append-only research/context records under
  `private/`; it does not authorize a saved review, target changes, transaction
  recording, order placement, publication, commit, or push.
- A private result is not overwritten without immediate explicit approval.
- Broker access and order placement remain prohibited regardless of approval.

The package is assembled from a literal public-file allowlist. The builder rejects
repository-local output, symlinks, hardlinks, unexpected files, ignored sources,
and inventory drift. See `docs/SECURITY.md` for the full boundary.

## Deliberate non-goals

This version does not provide:

- a Python live market-data provider or guaranteed real-time feed;
- broker connectivity or order execution;
- tax, legal, suitability, or personalized financial conclusions;
- return forecasts, autonomous monitoring, or background tasks;
- inference of missing market, portfolio, or policy data;
- unbounded agent debate or automatic target-policy changes;
- a general ChatGPT host, MCP service, or non-Codex multi-agent runtime.

SteadyFolio is not financial advice.

## Development and verification

Run the complete source-checkout gate from the repository root:

```powershell
python -m compileall -q src tests tools
python tools/generate_synthetic_example.py
python tools/generate_synthetic_intelligence.py
python tools/generate_synthetic_committee.py
python tools/generate_synthetic_equity.py
python tools/generate_synthetic_multi_agent.py
git diff --exit-code -- examples
python -m unittest discover -s tests -p "test_*.py"
python tools/run_repository_checks.py --require-gitleaks
git diff --check
```

Build the plugin only outside the repository, validate it, and compare it with the
tracked mirror:

```powershell
$buildRoot = Join-Path $env:TEMP "steadyfolio-plugin-0.3.1"
python tools/build_plugin.py --output $buildRoot
python path\to\plugin-creator\scripts\validate_plugin.py "$buildRoot\plugins\steadyfolio"
```

Create the deterministic installation archive outside the repository:

```powershell
$archive = Join-Path $env:TEMP "steadyfolio-0.3.1.zip"
python tools/build_release.py --output $archive
Get-FileHash -Algorithm SHA256 -LiteralPath $archive
```

`tools/build_release.py` writes sorted entries with fixed ZIP metadata, so identical
public source inputs produce byte-for-byte identical archives. A local archive or
plugin installation is not permission to publish it.

Architecture, calculations, research methodology, review contracts, operations,
and maintenance are documented under `docs/`. The project is licensed under the
MIT License.
