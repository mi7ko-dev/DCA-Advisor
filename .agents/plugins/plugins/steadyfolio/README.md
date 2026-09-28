# SteadyFolio Codex plugin

This self-contained plugin bundles the public SteadyFolio skill, deterministic
Python engine, schemas, documentation, and synthetic examples. It does not include
private portfolio state, credentials, live-provider access, broker connectivity,
trade execution, or tax/legal conclusions.

## Install from a repository checkout

From the repository root:

```powershell
codex plugin marketplace add ./.agents/plugins
codex plugin add steadyfolio@steadyfolio-local
```

Start a new Codex thread after installation and invoke `$steadyfolio`. Real user
state and every derived output must remain under an ignored `private/` workspace in
the active project, never inside the installed plugin.

Python 3.11 or newer is required for the bundled deterministic engine. The project
is licensed under the MIT License.
