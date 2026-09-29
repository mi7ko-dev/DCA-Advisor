"""Build the installable SteadyFolio Codex plugin from a public allowlist."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_NAME = "steadyfolio"
MARKETPLACE_NAME = "steadyfolio-local"
PLUGIN_VERSION = "0.2.0"

PUBLIC_SOURCE_FILES = (
    "LICENSE",
    "pyproject.toml",
    ".agents/skills/steadyfolio/SKILL.md",
    ".agents/skills/steadyfolio/agents/openai.yaml",
    ".agents/skills/steadyfolio/references/multi-agent-equity-review.md",
    ".agents/skills/steadyfolio/references/response-contract.md",
    ".agents/skills/steadyfolio/references/workflows.md",
    "docs/CALCULATIONS.md",
    "docs/COMMITTEE.md",
    "docs/EQUITY_REVIEW.md",
    "docs/MAINTENANCE.md",
    "docs/OPERATIONS.md",
    "docs/RESEARCH.md",
    "docs/SECURITY.md",
    "examples/committee-requests.example.json",
    "examples/contribution-request.example.json",
    "examples/equity-evidence.example.json",
    "examples/equity-portfolio.example.json",
    "examples/equity-review.example.json",
    "examples/equity-review.example.md",
    "examples/market-input.example.json",
    "examples/reports/multi-agent-equity-review.md",
    "examples/portfolio-policy-result.example.json",
    "examples/portfolio-policy-result.example.md",
    "examples/portfolio-policy.example.json",
    "examples/portfolio.example.json",
    "examples/reports/committee-workflows.md",
    "examples/reports/monthly-contribution.md",
    "examples/reports/portfolio-intelligence.md",
    "examples/reports/thesis-review.md",
    "examples/research-snapshot.example.json",
    "examples/results/analysis.example.json",
    "examples/results/committee-workflows.example.json",
    "examples/results/contribution-plan.example.json",
    "examples/results/intelligence.example.json",
    "examples/results/multi-agent-equity-review.example.json",
    "examples/results/multi-agent-eval.example.json",
    "examples/results/thesis-review.example.json",
    "examples/stress-windows.example.json",
    "examples/thesis-evidence.example.json",
    "schemas/analysis-result.schema.json",
    "schemas/agent-input-packet.schema.json",
    "schemas/committee-result.schema.json",
    "schemas/contribution-plan.schema.json",
    "schemas/equity-evidence.schema.json",
    "schemas/equity-review.schema.json",
    "schemas/intelligence-result.schema.json",
    "schemas/market-input.schema.json",
    "schemas/multi-agent-equity-review.schema.json",
    "schemas/portfolio-policy-result.schema.json",
    "schemas/portfolio-policy.schema.json",
    "schemas/portfolio.schema.json",
    "schemas/research-snapshot.schema.json",
    "schemas/specialist-result.schema.json",
    "schemas/thesis-review.schema.json",
    "src/steadyfolio/__init__.py",
    "src/steadyfolio/agent_models.py",
    "src/steadyfolio/calculations.py",
    "src/steadyfolio/committee.py",
    "src/steadyfolio/committee_models.py",
    "src/steadyfolio/committee_reporting.py",
    "src/steadyfolio/equity.py",
    "src/steadyfolio/equity_models.py",
    "src/steadyfolio/equity_reporting.py",
    "src/steadyfolio/equity_validation.py",
    "src/steadyfolio/errors.py",
    "src/steadyfolio/intelligence.py",
    "src/steadyfolio/intelligence_reporting.py",
    "src/steadyfolio/models.py",
    "src/steadyfolio/multi_agent.py",
    "src/steadyfolio/portfolio_policy.py",
    "src/steadyfolio/providers.py",
    "src/steadyfolio/reporting.py",
    "src/steadyfolio/research_models.py",
    "src/steadyfolio/research_validation.py",
    "src/steadyfolio/storage.py",
    "src/steadyfolio/thesis.py",
    "src/steadyfolio/validation.py",
    "tools/generate_synthetic_committee.py",
    "tools/generate_synthetic_equity.py",
    "tools/generate_synthetic_example.py",
    "tools/generate_synthetic_intelligence.py",
    "tools/generate_synthetic_multi_agent.py",
)

PLUGIN_MANIFEST = {
    "name": PLUGIN_NAME,
    "version": PLUGIN_VERSION,
    "description": (
        "Deterministic portfolio maintenance plus bounded host-native Codex "
        "subagents for evidence-limited equity review."
    ),
    "author": {
        "name": "mi7ko-dev",
        "url": "https://github.com/mi7ko-dev",
    },
    "homepage": "https://github.com/mi7ko-dev/DCA-Advisor",
    "repository": "https://github.com/mi7ko-dev/DCA-Advisor",
    "license": "MIT",
    "keywords": [
        "portfolio",
        "investing",
        "dca",
        "etf",
        "equity-review",
        "multi-agent",
    ],
    "skills": "./skills/",
    "interface": {
        "displayName": "SteadyFolio",
        "shortDescription": "Deterministic reviews with bounded equity agents",
        "longDescription": (
            "Run source-attributed contribution, portfolio, ETF thesis, overlap, "
            "and evidence-limited equity reviews. Equity review can use bounded "
            "Codex-native subagents; no workflow executes trades."
        ),
        "developerName": "SteadyFolio contributors",
        "category": "Finance",
        "capabilities": ["Interactive"],
        "defaultPrompt": "Review my portfolio with explicit evidence and limitations.",
    },
}

MARKETPLACE_MANIFEST = {
    "name": MARKETPLACE_NAME,
    "interface": {"displayName": "SteadyFolio Local"},
    "plugins": [
        {
            "name": PLUGIN_NAME,
            "source": {
                "source": "local",
                "path": f"./plugins/{PLUGIN_NAME}",
            },
            "policy": {
                "installation": "AVAILABLE",
                "authentication": "ON_INSTALL",
            },
            "category": "Finance",
        }
    ],
}

PLUGIN_README = """# SteadyFolio Codex plugin

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
"""


def _plugin_relative_path(source_relative: str) -> str:
    skill_prefix = ".agents/skills/steadyfolio/"
    if source_relative.startswith(skill_prefix):
        return "skills/steadyfolio/" + source_relative[len(skill_prefix) :]
    return source_relative


def expected_inventory() -> tuple[str, ...]:
    """Return the exact marketplace inventory emitted by this builder."""

    plugin_prefix = f"plugins/{PLUGIN_NAME}/"
    generated = {
        ".agents/plugins/marketplace.json",
        plugin_prefix + ".codex-plugin/plugin.json",
        plugin_prefix + "README.md",
    }
    generated.update(
        plugin_prefix + _plugin_relative_path(path) for path in PUBLIC_SOURCE_FILES
    )
    return tuple(sorted(generated))


def _tracked_files() -> set[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
    )
    return {
        item.decode("utf-8").replace("\\", "/")
        for item in result.stdout.split(b"\0")
        if item
    }


def _public_candidate_files() -> set[str]:
    result = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
    )
    return {
        item.decode("utf-8").replace("\\", "/")
        for item in result.stdout.split(b"\0")
        if item
    }


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, ensure_ascii=True, indent=2) + "\n")


def _reject_output_symlinks(output_root: Path) -> None:
    for component in (output_root, *output_root.parents):
        if component.is_symlink():
            raise RuntimeError("Plugin output cannot traverse a symlink.")
    if not output_root.exists():
        return
    for path in output_root.rglob("*"):
        if path.is_symlink():
            raise RuntimeError("Plugin output cannot contain symlinks.")
        if path.is_file() and path.stat().st_nlink > 1:
            raise RuntimeError("Plugin output cannot contain hardlinks.")


def build_plugin(output_root: Path) -> tuple[str, ...]:
    """Build a marketplace root and fail closed on source or inventory drift."""

    output_root = output_root.absolute()
    _reject_output_symlinks(output_root)
    output_root = output_root.resolve()
    repository_root = REPOSITORY_ROOT.resolve()
    if output_root == repository_root or output_root.is_relative_to(repository_root):
        raise ValueError(
            "Plugin output must be outside the repository in a temporary directory."
        )

    available_public_sources = _tracked_files() | _public_candidate_files()
    missing_or_ignored = sorted(
        set(PUBLIC_SOURCE_FILES) - available_public_sources
    )
    if missing_or_ignored:
        raise RuntimeError(
            "Plugin allowlist contains missing or ignored files: "
            + ", ".join(missing_or_ignored)
        )

    expected = set(expected_inventory())
    if output_root.exists():
        existing = {
            path.relative_to(output_root).as_posix()
            for path in output_root.rglob("*")
            if path.is_file()
        }
        unexpected = sorted(existing - expected)
        if unexpected:
            raise RuntimeError(
                "Plugin output contains files outside the allowlist: "
                + ", ".join(unexpected)
            )

    plugin_root = output_root / "plugins" / PLUGIN_NAME
    for source_relative in PUBLIC_SOURCE_FILES:
        source = REPOSITORY_ROOT / source_relative
        resolved = source.resolve()
        if not resolved.is_relative_to(repository_root) or not source.is_file():
            raise RuntimeError(f"Invalid plugin source file: {source_relative}")
        cursor = REPOSITORY_ROOT
        for part in Path(source_relative).parts:
            cursor /= part
            if cursor.is_symlink():
                raise RuntimeError(
                    f"Plugin source cannot traverse a symlink: {source_relative}"
                )
        destination = plugin_root / _plugin_relative_path(source_relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination, follow_symlinks=False)

    _write_json(
        output_root / ".agents" / "plugins" / "marketplace.json",
        MARKETPLACE_MANIFEST,
    )
    _write_json(plugin_root / ".codex-plugin" / "plugin.json", PLUGIN_MANIFEST)
    with (plugin_root / "README.md").open(
        "w", encoding="utf-8", newline="\n"
    ) as stream:
        stream.write(PLUGIN_README)

    _reject_output_symlinks(output_root)
    actual = {
        path.relative_to(output_root).as_posix()
        for path in output_root.rglob("*")
        if path.is_file()
    }
    if actual != expected:
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        raise RuntimeError(
            f"Plugin inventory mismatch; missing={missing}, unexpected={unexpected}"
        )
    return tuple(sorted(actual))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the SteadyFolio Codex plugin from public tracked files."
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Repository-shaped marketplace root to create or refresh.",
    )
    args = parser.parse_args()
    inventory = build_plugin(args.output)
    print(
        f"Built {PLUGIN_NAME} {PLUGIN_VERSION} with {len(inventory)} allowlisted files "
        f"at {args.output.resolve()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
