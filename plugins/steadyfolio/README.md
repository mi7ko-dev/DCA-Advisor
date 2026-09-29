# SteadyFolio Codex plugin

This self-contained plugin bundles the public SteadyFolio skill, deterministic
Python engine, bounded host-native Codex subagent protocol for equity review,
schemas, documentation, and synthetic examples. It does not include private
portfolio state, credentials, live-provider access, broker connectivity, trade
execution, or tax/legal conclusions.

The contribution route never starts agents. A Phase 8 equity review may start four
Codex specialist threads and one critic thread, which adds model-token use,
latency, and hosted processing of each role-minimal evidence packet. If host-native
subagents are unavailable, the plugin reports a deterministic-only fallback and
does not call it multi-agent. Packets exclude request and account identifiers,
source paths, raw provider payloads, and free-form portfolio notes; execution
metadata is attached by the host rather than accepted from model output.

## Install from a repository checkout

From the repository root:

```powershell
$pluginRoot = (Resolve-Path .\plugins\steadyfolio).Path
py -3.11 -S -c "import sys; sys.path.insert(0, r'$pluginRoot\src'); import steadyfolio; assert callable(steadyfolio.run_committee_workflow); assert callable(steadyfolio.prepare_multi_agent_equity_review)"
codex plugin marketplace add .
codex plugin add steadyfolio@steadyfolio-local
```

The Codex plugin command installs plugin files; it does not `pip install` the
bundled `src`-layout package. The installed skill resolves its runtime root and
prepends the bundled `src` path for direct engine imports. Start a new Codex thread
after installation and invoke `$steadyfolio`. Real user state and every derived
output must remain under an ignored `private/` workspace in the active project,
never inside the installed plugin.

Python 3.11 or newer is required for the bundled deterministic engine. The project
is licensed under the MIT License.
