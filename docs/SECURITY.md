# Security and Repository Safety

## Public repository boundary

This repository is public. Source code, deterministic tools, schemas, synthetic fixtures, and product documentation may be tracked. Real investor data and any output derived from it must remain outside Git under the ignored `private/` directory.

The boundary includes holdings, balances, transactions, goals, account identifiers, broker statements, personal notes, prompts containing private context, runtime memory, provider responses, query histories, reports, screenshots, and credentials. Public examples and tests must be created from scratch with synthetic data; they must never be anonymized copies of a real portfolio.

Ignore rules are a safety net, not a storage design. Application-owned private state belongs under `private/`, even when another ignored directory exists.

## Local and external processing

The repository-safety checker, tests, and Gitleaks run locally. The Gitleaks wrapper scans Git history and a temporary snapshot containing only files that Git currently considers public candidates. It does not scan ignored `private/` state or cloned blueprint repository content, follow symlinks, upload scan results, or retain the temporary snapshot. The public `blueprint/BLUEPRINT_SOURCES.md` metadata index remains part of the scan.

GitHub Actions receives only committed repository content. The repository-safety workflow uses synthetic path checks and read-only repository permissions. No private state, local scan report, or environment dump should be uploaded as an artifact.

Future market-data integrations must send only the minimum necessary instrument identifiers and parameters. They must not send holdings quantities, account identifiers, or personal goals without explicit authorization. Provider and host data flows must be documented before those integrations are enabled.

## Required checks

Run the complete local check from the repository root:

```powershell
python tools/run_repository_checks.py --require-gitleaks
```

The command verifies expected ignored paths, expected public paths, the Git index, synthetic unit tests, Git history, and current public candidate files. Secret findings are reported without printing detailed matches or candidate filenames.

Install the pinned Windows Gitleaks binary into the ignored local workspace when needed:

```powershell
powershell -ExecutionPolicy Bypass -File tools/install_gitleaks.ps1
```

The installer downloads Gitleaks 8.30.1 from the official release, verifies its pinned SHA-256 checksum, and extracts it only under `workspace/tools/gitleaks/`. It does not modify the system installation or global Git configuration.

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
