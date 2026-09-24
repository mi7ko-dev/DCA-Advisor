#!/usr/bin/env python3
"""Run local public-repository checks without scanning ignored private state."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class PublicCandidate:
    """A public path backed by either an index blob or an untracked file."""

    relative_path: Path
    index_blob: str | None


def _run(arguments: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(arguments),
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _run_bytes(
    arguments: Sequence[str], cwd: Path
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        list(arguments),
        cwd=cwd,
        capture_output=True,
        check=False,
    )


def _print_failure(label: str, result: subprocess.CompletedProcess[str]) -> None:
    print(f"{label} failed.", file=sys.stderr)
    output = (result.stdout + result.stderr).strip()
    if output:
        print(output, file=sys.stderr)


def run_python_checks(repo_root: Path) -> bool:
    safety = _run(
        (sys.executable, "tools/repository_safety.py", "--repo-root", str(repo_root)),
        repo_root,
    )
    if safety.returncode != 0:
        _print_failure("Repository safety check", safety)
        return False
    print(safety.stdout.strip())

    tests = _run(
        (
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            "-p",
            "test_*.py",
        ),
        repo_root,
    )
    if tests.returncode != 0:
        _print_failure("Repository safety tests", tests)
        return False
    print("Repository safety tests passed.")
    return True


def find_gitleaks(repo_root: Path) -> Path | None:
    executable_name = "gitleaks.exe" if sys.platform == "win32" else "gitleaks"
    local_candidate = repo_root / "workspace" / "tools" / "gitleaks" / executable_name
    if local_candidate.is_file():
        return local_candidate
    path_candidate = shutil.which("gitleaks")
    return Path(path_candidate) if path_candidate else None


def _relative_git_path(raw_path: bytes) -> Path:
    relative_path = Path(os.fsdecode(raw_path))
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise RuntimeError("Git returned a path outside the repository.")
    return relative_path


def public_candidate_files(repo_root: Path) -> list[PublicCandidate]:
    """Return exact staged blobs plus public untracked working-tree files."""

    indexed = _run_bytes(("git", "ls-files", "--stage", "-z"), repo_root)
    if indexed.returncode != 0:
        raise RuntimeError("Git could not enumerate indexed public files.")

    candidates: list[PublicCandidate] = []
    indexed_paths: set[Path] = set()
    for entry in indexed.stdout.split(b"\0"):
        if not entry:
            continue
        try:
            metadata, raw_path = entry.split(b"\t", 1)
            mode, object_id, stage = metadata.split()
        except ValueError as error:
            raise RuntimeError("Git returned malformed index metadata.") from error

        if stage != b"0":
            raise RuntimeError("The Git index contains unresolved merge entries.")

        relative_path = _relative_git_path(raw_path)
        indexed_paths.add(relative_path)
        if mode == b"120000":
            raise RuntimeError(
                "A public indexed candidate is a symlink; refusing to follow it."
            )
        if mode == b"160000":
            continue
        if mode not in (b"100644", b"100755"):
            raise RuntimeError("Git returned an unsupported public index entry.")

        blob = object_id.decode("ascii")
        candidates.append(
            PublicCandidate(
                relative_path=relative_path,
                index_blob=None if set(blob) == {"0"} else blob,
            )
        )

    untracked = _run_bytes(
        ("git", "ls-files", "--others", "--exclude-standard", "-z"),
        repo_root,
    )
    if untracked.returncode != 0:
        raise RuntimeError("Git could not enumerate public untracked files.")
    for raw_path in untracked.stdout.split(b"\0"):
        if not raw_path:
            continue
        relative_path = _relative_git_path(raw_path)
        if relative_path not in indexed_paths:
            candidates.append(PublicCandidate(relative_path, None))

    return sorted(candidates, key=lambda candidate: candidate.relative_path.as_posix())


def _reject_worktree_symlink(repo_root: Path, relative_path: Path) -> None:
    current = repo_root
    for part in relative_path.parts:
        current /= part
        if current.is_symlink():
            raise RuntimeError(
                "A public untracked candidate is a symlink; refusing to follow it."
            )


def create_public_scan_snapshot(repo_root: Path, destination: Path) -> int:
    copied = 0
    for candidate in public_candidate_files(repo_root):
        target = destination / candidate.relative_path
        target.parent.mkdir(parents=True, exist_ok=True)

        if candidate.index_blob is not None:
            blob = _run_bytes(
                ("git", "cat-file", "blob", candidate.index_blob), repo_root
            )
            if blob.returncode != 0:
                raise RuntimeError("Git could not read an indexed public file.")
            target.write_bytes(blob.stdout)
        else:
            _reject_worktree_symlink(repo_root, candidate.relative_path)
            source = repo_root / candidate.relative_path
            if not source.is_file():
                continue
            shutil.copyfile(source, target, follow_symlinks=False)
        copied += 1
    return copied


def run_gitleaks(repo_root: Path, executable: Path) -> bool:
    version = _run((str(executable), "version"), repo_root)
    if version.returncode != 0:
        print("Gitleaks version check failed.", file=sys.stderr)
        return False

    history = _run(
        (str(executable), "git", "--redact", "--no-banner", str(repo_root)),
        repo_root,
    )
    if history.returncode != 0:
        print(
            "Gitleaks detected a potential secret in Git history; detailed output is suppressed.",
            file=sys.stderr,
        )
        return False

    with tempfile.TemporaryDirectory(prefix="steadyfolio-public-scan-") as temporary:
        snapshot = Path(temporary)
        try:
            copied = create_public_scan_snapshot(repo_root, snapshot)
        except RuntimeError as error:
            print(f"Public candidate scan could not run: {error}", file=sys.stderr)
            return False
        current = _run(
            (str(executable), "dir", "--redact", "--no-banner", str(snapshot)),
            repo_root,
        )
        if current.returncode != 0:
            print(
                "Gitleaks detected a potential secret in public candidate files; "
                "detailed output is suppressed.",
                file=sys.stderr,
            )
            return False

    print(
        f"Gitleaks {version.stdout.strip()} passed for Git history and "
        f"{copied} public candidate files."
    )
    return True


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-gitleaks",
        action="store_true",
        help="Fail if Gitleaks is not installed locally or available on PATH.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    if not run_python_checks(REPOSITORY_ROOT):
        return 1

    gitleaks = find_gitleaks(REPOSITORY_ROOT)
    if gitleaks is None:
        message = (
            "Gitleaks is unavailable. Run tools/install_gitleaks.ps1 or install it on PATH."
        )
        if args.require_gitleaks:
            print(message, file=sys.stderr)
            return 1
        print(f"Warning: {message}")
        return 0

    return 0 if run_gitleaks(REPOSITORY_ROOT, gitleaks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
