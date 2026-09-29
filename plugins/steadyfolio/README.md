# SteadyFolio Codex plugin

This self-contained plugin bundles the public SteadyFolio skill, deterministic
Python engine, bounded host-native research and subagent protocols, schemas,
documentation, and synthetic examples. It does not include private portfolio
state, credentials, a Python live-provider adapter, broker connectivity, trade
execution, background monitoring, or tax/legal conclusions.

Plugin version: `0.3.0`.

The contribution route never starts agents by default. A consequential review may
start two to four Codex specialist threads and one critic thread, which adds
model-token use, latency, and hosted processing of each role-minimal evidence
packet. The lead may first perform one foreground web research pass when current
facts are material, reusing adequate immutable records under `private/research/`.
If host-native subagents are unavailable, the plugin reports a deterministic or
sequential fallback and does not call it multi-agent. Packets exclude request and
account identifiers, source paths, raw provider payloads, and free-form portfolio
notes. Equity source IDs are replaced with packet-local opaque aliases; execution
metadata is attached by the host rather than accepted from model output.

## Install from a repository checkout

From the repository root:

```powershell
$pluginRoot = (Resolve-Path .\plugins\steadyfolio).Path
py -3.11 -B -S -c "import sys; sys.path.insert(0, r'$pluginRoot\src'); import steadyfolio; assert callable(steadyfolio.run_committee_workflow); assert callable(steadyfolio.prepare_multi_agent_equity_review)"
codex plugin marketplace add .
codex plugin add steadyfolio@steadyfolio-local
codex plugin list
```

## Install from the release archive

The archive is named `steadyfolio-0.3.0.zip` and contains the
marketplace root directly. From the directory containing the archive:

```powershell
$archive = (Resolve-Path .\steadyfolio-0.3.0.zip).Path
$installRoot = Join-Path (Get-Location) "steadyfolio-0.3.0"
New-Item -ItemType Directory -Path $installRoot | Out-Null
Expand-Archive -LiteralPath $archive -DestinationPath $installRoot
Set-Location $installRoot
$pluginRoot = (Resolve-Path .\plugins\steadyfolio).Path
py -3.11 -B -S -c "import sys; sys.path.insert(0, r'$pluginRoot\src'); import steadyfolio; assert callable(steadyfolio.run_committee_workflow); assert callable(steadyfolio.prepare_multi_agent_equity_review)"
codex plugin marketplace add .
codex plugin add steadyfolio@steadyfolio-local
codex plugin list
```

For an update, replace the checkout or extract the new archive into a new
directory, register that marketplace root, and rerun `codex plugin add`. Start a
new Codex thread after every install or update.

The Codex plugin command installs plugin files; it does not `pip install` the
bundled `src`-layout package. The installed skill resolves its runtime root and
prepends the bundled `src` path for direct engine imports. Start a new Codex thread
after installation and invoke `$steadyfolio`. Real user state and every derived
output must remain under an ignored `private/` workspace in the active project,
never inside the installed plugin.

Python 3.11 or newer is required for the bundled deterministic engine. The project
is licensed under the MIT License.
