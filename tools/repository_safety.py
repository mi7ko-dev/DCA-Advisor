#!/usr/bin/env python3
"""Validate SteadyFolio's public-repository boundary using Git itself."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import subprocess
import sys
from typing import Iterable, Sequence


IGNORED_PATHS: tuple[str, ...] = (
    "private/portfolio/portfolio.json",
    "private/reports/review.md",
    "private/sessions/session.json",
    "agent_memory/session.json",
    "conversation_history/thread.json",
    "blueprint/cofolio/README.md",
    "workspace/scratch.txt",
    ".env",
    ".env.production",
    "app.env.local",
    "credentials.json",
    "cache/prices.sqlite",
    "cache/prices.sqlite-wal",
    "outputs/report.md",
)

TRACKABLE_PATHS: tuple[str, ...] = (
    "README.md",
    "AGENTS.md",
    ".gitignore",
    ".env.example",
    "blueprint/BLUEPRINT_SOURCES.md",
    ".agents/skills/steadyfolio/SKILL.md",
    ".agents/skills/steadyfolio/agents/openai.yaml",
    "schemas/portfolio.schema.json",
    "examples/portfolio.example.json",
    "examples/reports/monthly-contribution.md",
    "tests/fixtures/synthetic-portfolio.json",
    "docs/ARCHITECTURE.md",
)

PUBLIC_BLUEPRINT_PATHS = frozenset({"blueprint/BLUEPRINT_SOURCES.md"})

FORBIDDEN_TRACKED_ROOTS = frozenset(
    {
        "private",
        "local",
        "user-data",
        "user_data",
        "personal",
        "state",
        "sessions",
        "session",
        "history",
        "agent-memory",
        "agent_memory",
        "conversation-history",
        "conversation_history",
        "blueprint",
        "workspace",
        "workdir",
        "worktrees",
        ".worktrees",
        "scratch",
        "tmp",
        "temp",
        "cache",
        ".cache",
        "downloads",
        "logs",
        "run",
        "runtime",
        "outputs",
        "reports",
        "generated",
        "artifacts",
        "backup",
        "backups",
        "secrets",
        "credentials",
        "databases",
    }
)


@dataclass(frozen=True)
class IndexReport:
    tracked_count: int
    ignored_tracked_count: int
    forbidden_tracked_count: int

    @property
    def is_safe(self) -> bool:
        return self.ignored_tracked_count == 0 and self.forbidden_tracked_count == 0


def _run_git(repo_root: Path, arguments: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


def assert_git_repository(repo_root: Path) -> None:
    result = _run_git(repo_root, ("rev-parse", "--show-toplevel"))
    if result.returncode != 0:
        raise RuntimeError("The selected directory is not a Git repository.")
    actual_root = Path(result.stdout.strip()).resolve()
    if actual_root != repo_root.resolve():
        raise RuntimeError("Run the safety check from the repository root.")


def is_ignored(repo_root: Path, relative_path: str) -> bool:
    result = _run_git(
        repo_root,
        ("check-ignore", "--quiet", "--no-index", "--", relative_path),
    )
    if result.returncode not in (0, 1):
        raise RuntimeError("Git could not evaluate an ignore rule.")
    return result.returncode == 0


def _split_nul(value: str) -> list[str]:
    return [item for item in value.split("\0") if item]


def tracked_files(repo_root: Path) -> list[str]:
    result = _run_git(repo_root, ("ls-files", "-z"))
    if result.returncode != 0:
        raise RuntimeError("Git could not inspect the repository index.")
    return _split_nul(result.stdout)


def ignored_tracked_files(repo_root: Path) -> list[str]:
    result = _run_git(
        repo_root,
        ("ls-files", "--cached", "--ignored", "--exclude-standard", "-z"),
    )
    if result.returncode != 0:
        raise RuntimeError("Git could not inspect tracked files against ignore rules.")
    return _split_nul(result.stdout)


def is_explicitly_forbidden(relative_path: str) -> bool:
    path = PurePosixPath(relative_path.replace("\\", "/"))
    if not path.parts:
        return False
    if path.as_posix() in PUBLIC_BLUEPRINT_PATHS:
        return False
    if path.parts[0] in FORBIDDEN_TRACKED_ROOTS:
        return True
    if relative_path == ".env" or relative_path.startswith(".env."):
        return relative_path != ".env.example"
    return False


def inspect_index(repo_root: Path) -> IndexReport:
    tracked = tracked_files(repo_root)
    ignored_tracked = ignored_tracked_files(repo_root)
    forbidden_tracked = [path for path in tracked if is_explicitly_forbidden(path)]
    return IndexReport(
        tracked_count=len(tracked),
        ignored_tracked_count=len(ignored_tracked),
        forbidden_tracked_count=len(forbidden_tracked),
    )


def evaluate_expectations(
    repo_root: Path,
    ignored_paths: Iterable[str] = IGNORED_PATHS,
    trackable_paths: Iterable[str] = TRACKABLE_PATHS,
) -> list[str]:
    failures: list[str] = []
    for relative_path in ignored_paths:
        if not is_ignored(repo_root, relative_path):
            failures.append(f"Expected ignored path is trackable: {relative_path}")
    for relative_path in trackable_paths:
        if is_ignored(repo_root, relative_path):
            failures.append(f"Expected public path is ignored: {relative_path}")
    return failures


def run_checks(repo_root: Path) -> list[str]:
    assert_git_repository(repo_root)
    failures = evaluate_expectations(repo_root)
    index_report = inspect_index(repo_root)
    if index_report.ignored_tracked_count:
        failures.append(
            "The index contains tracked files that match ignore rules "
            f"(count: {index_report.ignored_tracked_count}; paths redacted)."
        )
    if index_report.forbidden_tracked_count:
        failures.append(
            "The index contains files under forbidden private/runtime roots "
            f"(count: {index_report.forbidden_tracked_count}; paths redacted)."
        )
    return failures


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root to inspect (defaults to this tool's repository).",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    repo_root = args.repo_root.resolve()
    try:
        failures = run_checks(repo_root)
        index_report = inspect_index(repo_root)
    except (OSError, RuntimeError) as error:
        print(f"Repository safety check could not run: {error}", file=sys.stderr)
        return 2

    if failures:
        print("Repository safety check failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print(
        "Repository safety check passed: "
        f"{len(IGNORED_PATHS)} ignored-path expectations, "
        f"{len(TRACKABLE_PATHS)} public-path expectations, and "
        f"{index_report.tracked_count} tracked files inspected."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
