# Operations Guide

## Supported installation

SteadyFolio supports Python 3.11 or newer and the repo-local Codex skill in this
repository. It also provides a self-contained local Codex plugin. Neither mode has
a runtime dependency outside the Python standard library.

Phase 8 equity review additionally requires a Codex host release with native
subagents enabled. It does not require an OpenAI API key or Agents SDK dependency.
Each real run starts up to four specialist model contexts and one critic context,
so it consumes more host tokens and latency than deterministic fallback. The
contribution route never starts agents.

From the repository root on Windows:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install --no-deps .
.venv\Scripts\python -c "import steadyfolio; assert callable(steadyfolio.run_committee_workflow); assert callable(steadyfolio.prepare_multi_agent_equity_review)"
```

Opening the repository in Codex makes the skill at
`.agents/skills/steadyfolio/SKILL.md` available to that repository context. Invoke
it explicitly with `$steadyfolio` when deterministic portfolio routing is wanted.
The current repository session has discovered the skill, and its files pass the
bundled skill validator.

To install the plugin from a checkout, first verify the bundled runtime through its
explicit source path, then register the repository marketplace and add the plugin.
The Codex plugin command installs plugin files; it does not `pip install` the
bundled `src`-layout package.

```powershell
$pluginRoot = (Resolve-Path .\plugins\steadyfolio).Path
py -3.11 -S -c "import sys; sys.path.insert(0, r'$pluginRoot\src'); import steadyfolio; assert callable(steadyfolio.run_committee_workflow); assert callable(steadyfolio.prepare_multi_agent_equity_review)"
codex plugin marketplace add .
codex plugin add steadyfolio@steadyfolio-local
```

Start a new Codex thread after installation. The plugin manifest and skill pass the
bundled validators. The installed skill resolves its plugin runtime root and applies
the same explicit `src` bootstrap before direct imports, so it does not depend on a
separate SteadyFolio installation or ambient `PYTHONPATH`. A general ChatGPT host,
MCP service, and clean-machine cross-platform installation are not claimed.

No environment variable or credential is required for the implemented offline
core. Do not add broker or provider keys for this version. If a future adapter is
approved, keep credentials in an ignored local `.env` or an operating-system secret
store and document the minimum variables without committing values.

## Synthetic walkthrough

The public profile, holdings, goals, market observations, and research evidence in
`examples/` are entirely synthetic. Start with:

- `examples/portfolio.example.json` for the investor profile, targets, accounts,
  instruments, holdings, transactions, and theses;
- `examples/market-input.example.json` for dated synthetic prices and FX;
- `examples/contribution-request.example.json` for the EUR 400 contribution and
  trading constraints; and
- the research, stress-window, and thesis-evidence examples for intelligence and
  committee routes; and
- `examples/equity-portfolio.example.json`,
  `examples/equity-evidence.example.json`, and
  `examples/portfolio-policy.example.json` for the offline equity and policy route.

Regenerate the contribution result, intelligence result, thesis review, and six
committee demonstrations:

```powershell
python tools/generate_synthetic_example.py
python tools/generate_synthetic_intelligence.py
python tools/generate_synthetic_committee.py
python tools/generate_synthetic_equity.py
python tools/generate_synthetic_multi_agent.py
git diff --exit-code -- examples
```

The first generator demonstrates valuation and both contribution strategies. The
third demonstrates contribution, portfolio review, thesis review, partial overlap,
residual drift, and missing or stale evidence. Inspect the paired JSON in
`examples/results/` and Markdown in `examples/reports/`.

The fourth generator produces the Phase 7 equity review and portfolio-policy JSON
and Markdown examples directly under `examples/`.

The fifth generator produces a synthetic Phase 8 in-memory agent-contract result,
Markdown report, and defect-code eval. It does not make model or network calls and
must not be reported as a live multi-agent execution.

To request the same routes conversationally, use `$steadyfolio` with a narrow
request such as:

```text
Use $steadyfolio to plan a synthetic EUR 400 monthly contribution.
Use $steadyfolio to review whether the synthetic global ETF thesis still holds.
Use $steadyfolio to run an equity review from the supplied synthetic evidence.
```

The skill must use the engine output. It must not calculate portfolio values in
prose, invent a missing price or FX rate, or turn an analysis request into approval
to save or execute anything.

For equity review, the skill first creates immutable packets in memory, then asks
Codex to start one subagent for each specialist and one later critic. If the host
cannot start subagents, it uses `run_deterministic_equity_fallback` and reports
`runtime_type=none`. Do not describe `in_memory_test_backend` or the fallback as a
real multi-agent run.

## Private-state initialization

Choose the workspace root explicitly. The storage layer creates and writes only
below its `private/` child, validates the complete state, rejects unsafe filenames
and symlinks, writes atomically, and refuses overwrite by default. If the workspace
is inside a Git worktree, the exact private target must be ignored and untracked
before any directory is created or any value is read or written.

```python
import json
from pathlib import Path

from steadyfolio.storage import initialize_workspace, load_state
from steadyfolio.validation import state_from_dict

workspace = Path(r"C:\path\to\an\explicit\workspace")
private_import = workspace / "private" / "imports" / "portfolio.json"
state = state_from_dict(json.loads(private_import.read_text(encoding="utf-8")))
state_path = initialize_workspace(workspace, state)
assert load_state(workspace) == state
print(state_path)  # .../private/portfolio/portfolio.json
```

The import file in this example is already private. A source file may instead live
outside the public repository. Never stage a real input, generated result, prompt,
provider response, or report. Retain backups outside the repository according to
the user's own retention and encryption policy. The MVP does not supply backup,
encryption, migration, concurrent-write, or deletion automation.

The API requires a separate explicit call to save a result or review. Do not use
`overwrite=True` without immediate user approval. Saving a review does not mutate
portfolio state, approve a target change, or record a transaction.

Phase 7 equity and policy outputs use `save_equity_review` and
`save_portfolio_policy_result`. Both validate the structured result, write below
`private/reviews/`, and refuse overwrite by default. Creating or replacing a real
policy instance is a separate approval-gated operation and is not implemented by
these result-saving functions.

## Data flow and provider boundary

```text
private validated state + explicit dated inputs
                    |
                    v
        deterministic local Python core
                    |
          structured result in memory
             /                 \
            v                   v
    answer in local host   approved private save

role-minimal equity packet
            |
            v
 Codex hosted specialist context x4
            |
            v
 Codex hosted critic context x1
            |
            v
 host-attached execution metadata
            |
            v
 validated lead synthesis in memory

public instrument/listing IDs + explicit evidence-source IDs + as-of date
                    |
                    v
       selected research-provider boundary
                    |
                    v
validated facts with provenance and coverage
```

The implemented provider is an offline synthetic provider. It receives only public
instrument/listing identifiers, explicitly referenced public evidence-source IDs,
and an as-of date. There is no live network adapter. A provider failure stops the
evidence-dependent route after one attempt, returns a generic limitation, and does
not expose the raw exception text in the result.

## Checks and troubleshooting

The following checks are source-checkout-only; the installed plugin intentionally
omits tests, build scripts, hooks, and repository-safety tooling. Run the full local
gate from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File tools/install_gitleaks.ps1
python tools/run_repository_checks.py --require-gitleaks
# Substitute the validator path from the local Codex installation.
python path\to\quick_validate.py .agents\skills\steadyfolio
```

The portable structural coverage also runs in `tests/test_skill.py`.

Common stops are intentional:

- a missing price, FX rate, target version, source date, or required coverage must
  be supplied rather than inferred;
- an equity ISIN, name, or listing mismatch stops before scoring;
- stale or incomplete evidence may produce `insufficient_evidence`;
- an existing private output is not overwritten by default;
- any symlink in a private output path is rejected; and
- a live provider, broker, or trade request is outside the implemented boundary.

See `docs/CALCULATIONS.md`, `docs/RESEARCH.md`, and `docs/COMMITTEE.md` for the exact
calculation, evidence, and bounded-review contracts.
