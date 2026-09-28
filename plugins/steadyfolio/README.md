# SteadyFolio Codex plugin

This self-contained plugin bundles the public SteadyFolio skill, deterministic
Python engine, schemas, documentation, and synthetic examples. It does not include
private portfolio state, credentials, live-provider access, broker connectivity,
trade execution, or tax/legal conclusions.

## Install from a repository checkout

From the repository root:

```powershell
$pluginRoot = (Resolve-Path .\plugins\steadyfolio).Path
py -3.11 -S -c "import sys; sys.path.insert(0, r'$pluginRoot\src'); import steadyfolio; assert callable(steadyfolio.run_committee_workflow)"
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
